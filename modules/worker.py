import sys
from queue import Queue
from threading import Lock

import config

from .attack import attack_credentials, attack_route, get_screenshot
from .rtsp import RTSPClient
from .utils import append_result

sys.path.append("..")


GLOBAL_LOCK = Lock()


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_route(target)
        if result:
            config.progress_bar.add_total(config.BRUTE_PROGRESS)
            output_queue.put(result)

        config.progress_bar.update(config.CHECK_PROGRESS, advance=1)
        input_queue.task_done()


def brute_credentials(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_credentials(target)
        if result:
            config.progress_bar.add_total(config.SCREENSHOT_PROGRESS)
            output_queue.put(target)

        config.progress_bar.update(config.BRUTE_PROGRESS, advance=1)
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

        config.progress_bar.update(config.SCREENSHOT_PROGRESS, advance=1)
        input_queue.task_done()
