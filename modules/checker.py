from modules import utils
import threading
from queue import Queue

from .attack import attack_route
from .rtsp import RTSPClient


class CheckerThread(threading.Thread):
    """
    Attempts to guess the provided target streaming routes and
    authentication types (basic auth, digest or none at all).
    """

    def __init__(self, check_queue: Queue, brute_queue: Queue) -> None:
        threading.Thread.__init__(self)
        self.check_queue = check_queue
        self.brute_queue = brute_queue

    def run(self) -> None:
        while True:
            target: RTSPClient = self.check_queue.get()

            result = attack_route(target)
            if result:
                utils.detect_auth_method(result)
                self.brute_queue.put(result)

            self.check_queue.task_done()
