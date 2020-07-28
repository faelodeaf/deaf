import sys
from threading import Lock
from queue import Queue

sys.path.append("..")
import config

from .attack import attack_route, attack_credentials, get_screenshot
from .rtsp import RTSPClient
from .utils import append_result

GLOBAL_LOCK = Lock()


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_route(target)
        if result:
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
            append_result(
                GLOBAL_LOCK, config.RESULT_FILE, config.HTML_FILE, image, target
            )

        input_queue.task_done()
