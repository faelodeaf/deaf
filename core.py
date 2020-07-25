import logging
import threading
from queue import Queue
from typing import List

import av
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
    logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(funcName)s] %(message)s"
    )
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
# This disables ValueError from av module printing to console, but this also
# means we won't get any logs from av, if they aren't FATAL or PANIC level.
av.logging.set_level(av.logging.FATAL)


def start_threads(number, target, *args):
    debugger.debug(f"Starting {number} threads of {target.__module__}.{target.__name__}")
    threads = []
    for _ in range(number):
        thread = threading.Thread(target=target, args=args)
        threads.append(thread)
        thread.start()
    return threads


def wait_for(queue: Queue, threads: List[threading.Thread]):
    """Waits for queue and then threads to finish."""
    queue.join()
    [queue.put(None) for _ in range(len(threads))]
    [t.join() for t in threads]


if __name__ == "__main__":
    init()

    config.CREDENTIALS = utils.load_txt("credentials.txt", "credentials")
    config.ROUTES = utils.load_txt("routes.txt", "routes")
    config.TARGETS = utils.load_txt("hosts.txt", "targets")

    utils.create_folder(config.PICS_FOLDER)
    utils.create_file(config.RESULT_FILE)
    utils.generate_html(config.HTML_FILE)

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    check_threads = start_threads(
        config.CHECK_THREADS, worker.brute_routes, check_queue, brute_queue
    )
    brute_threads = start_threads(
        config.BRUTE_THREADS, worker.brute_credentials, brute_queue, screenshot_queue
    )
    screenshot_threads = start_threads(
        config.SCREENSHOT_THREADS, worker.screenshot_targets, screenshot_queue
    )

    logging.info(f"{Fore.GREEN}Starting...\n{Style.RESET_ALL}")

    for ip in config.TARGETS:
        check_queue.put(RTSPClient(ip))

    wait_for(check_queue, check_threads)
    debugger.debug("Check queue and threads finished")
    wait_for(brute_queue, brute_threads)
    debugger.debug("Brute queue and threads finished")
    wait_for(screenshot_queue, screenshot_threads)
    debugger.debug("Screenshot queue and threads finished")

    print()
    file_handler.close()
    config.DEBUG_LOG_FILE.rename(config.REPORT_FOLDER / config.DEBUG_LOG_FILE.name)
    screenshots = list(config.PICS_FOLDER.iterdir())
    logging.info(f"{Fore.GREEN}Saved {len(screenshots)} screenshots{Style.RESET_ALL}")
    logging.info(
        f"{Fore.GREEN}Report available at {str(config.REPORT_FOLDER)}{Style.RESET_ALL}"
    )

