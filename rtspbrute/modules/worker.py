from queue import Queue
from threading import Lock

from rich.progress import TaskID

from .attack import attack_credentials, attack_route, get_screenshot
from .cli.output import ProgressBar
from .rtsp import RTSPClient
from .utils import append_result

PROGRESS_BAR: ProgressBar
CHECK_PROGRESS: TaskID
BRUTE_PROGRESS: TaskID
SCREENSHOT_PROGRESS: TaskID
GLOBAL_LOCK = Lock()


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_route(target)
        if result:
            PROGRESS_BAR.add_total(BRUTE_PROGRESS)
            output_queue.put(result)

        PROGRESS_BAR.update(CHECK_PROGRESS, advance=1)
        input_queue.task_done()


def brute_credentials(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        result = attack_credentials(target)
        if result:
            PROGRESS_BAR.add_total(SCREENSHOT_PROGRESS)
            output_queue.put(target)

        PROGRESS_BAR.update(BRUTE_PROGRESS, advance=1)
        input_queue.task_done()


def screenshot_targets(input_queue: Queue) -> None:
    while True:
        target: RTSPClient = input_queue.get()
        if target is None:
            break

        image = get_screenshot(target)
        if image:
            append_result(GLOBAL_LOCK, image, target)

        PROGRESS_BAR.update(SCREENSHOT_PROGRESS, advance=1)
        input_queue.task_done()
