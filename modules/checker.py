import threading

import sys
sys.path.append('..')

import config
from .rtsp import RTSPClient


class CheckerThread(threading.Thread):
    """
    Checks if given ip is available and tries to brute directories of it.
    """
    def __init__(self, check_queue, brute_queue):
        threading.Thread.__init__(self)
        self.check_queue = check_queue
        self.brute_queue = brute_queue

    def check(self, ip):
        with RTSPClient(ip, port=config.PORT, timeout=config.SOCKET_TIMEOUT) as client:
            for path in config.DIRECTORIES:
                client.create_packet(path)
                client.send_packet()
                if client.is_available():
                    self.brute_queue.put((ip, path))
                    config.update_bar(__class__)
                    break

    def run(self):
        while True:
            ip = self.check_queue.get()
            self.check(ip)
            config.update_bar(__class__, main=True)
            self.check_queue.task_done()
