import threading
from queue import Queue

from .attack import attack_credentials
from .rtsp import RTSPClient


class BruteThread(threading.Thread):
    """
    Brutes given ip to gain access to the stream.
    """

    def __init__(self, brute_queue: Queue, screenshot_queue: Queue) -> None:
        threading.Thread.__init__(self)
        self.brute_queue = brute_queue
        self.screenshot_queue = screenshot_queue

    def run(self) -> None:
        while True:
            target: RTSPClient = self.brute_queue.get()

            result = attack_credentials(target)
            if result:
                self.screenshot_queue.put(target)

            self.brute_queue.task_done()

