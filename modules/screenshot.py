import sys
import threading
from queue import Queue

sys.path.append("..")
import config

from .attack import get_screenshot
from .rtsp import RTSPClient
from .utils import append_result


class ScreenshotThread(threading.Thread):
    """
    Uses PyAV for capturing RTSP stream and taking screenshot.
    """

    def __init__(self, screenshot_queue: Queue) -> None:
        threading.Thread.__init__(self)
        self.screenshot_queue = screenshot_queue

    def run(self) -> None:
        while True:
            target: RTSPClient = self.screenshot_queue.get()

            image = get_screenshot(target)
            if image:
                append_result(config.RESULT_FILE, config.HTML_FILE, image, target)

            self.screenshot_queue.task_done()
