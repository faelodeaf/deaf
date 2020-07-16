import logging
from logging import Formatter
import time
from pathlib import Path
from queue import Queue

from colorama import init, Fore, Style

import config
from modules import *

# Logging module set up
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s",
)
debugger = logging.getLogger("debugger")
debugger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(config.DEBUG_LOG_FILE, "w")
file_handler.setFormatter(
    logging.Formatter("[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s")
)
debugger.addHandler(file_handler)
debugger.propagate = False

# Redirect PyAV logs only to file
libav_logger = logging.getLogger("libav")
libav_logger.setLevel(logging.DEBUG)
libav_logger.addHandler(file_handler)
libav_logger.propagate = False
av_logger = logging.getLogger("av")
av_logger.setLevel(logging.DEBUG)
av_logger.addHandler(file_handler)
av_logger.propagate = False


if __name__ == "__main__":
    init()
    start_datetime = time.strftime("%Y.%m.%d-%H.%M.%S")

    config.CREDENTIALS = utils.load_txt("credentials.txt", "credentials")
    config.ROUTES = utils.load_txt("routes.txt", "routes")
    config.TARGETS = utils.load_txt("hosts.txt", "targets")
    logging.info(f"{Fore.GREEN}Starting...\n{Style.RESET_ALL}")

    utils.create_folder(config.PICS_FOLDER)
    utils.create_file(config.RESULT_FILE)

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    check_threads = []
    brute_threads = []
    screenshot_threads = []

    for _ in range(config.CHECK_THREADS):
        check_worker = CheckerThread(check_queue, brute_queue)
        check_worker.daemon = True
        check_worker.start()
        check_threads.append(check_worker)

    for _ in range(config.BRUTE_THREADS):
        brute_worker = BruteThread(brute_queue, screenshot_queue)
        brute_worker.daemon = True
        brute_worker.start()
        brute_threads.append(brute_worker)

    for _ in range(config.SCREENSHOT_THREADS):
        screenshot_worker = ScreenshotThread(screenshot_queue)
        screenshot_worker.daemon = True
        screenshot_worker.start()
        screenshot_threads.append(screenshot_worker)

    for ip in config.TARGETS:
        check_queue.put(RTSPClient(ip))

    check_queue.join()
    [t.join for t in check_threads]
    brute_queue.join()
    [t.join for t in brute_threads]
    screenshot_queue.join()
    [t.join for t in screenshot_threads]

    print()
    file_handler.close()
    screenshots = list(config.PICS_FOLDER.iterdir())
    logging.info(f"{Fore.GREEN}Saved {len(screenshots)} screenshots{Style.RESET_ALL}")
    logging.info(f"{Fore.GREEN}Report available at {str(config.REPORTS_FOLDER / start_datetime)}{Style.RESET_ALL}")
    utils.save_result(
        config.REPORTS_FOLDER / f"{start_datetime}",
        config.PICS_FOLDER,
        config.DEBUG_LOG_FILE,
        config.RESULT_FILE,
    )
    utils.generate_html(config.REPORTS_FOLDER / f"{start_datetime}", config.REPORTS_FOLDER / f"{start_datetime}" / config.PICS_FOLDER.name)

