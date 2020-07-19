import logging
from queue import Queue

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
# This disables ValueError from av module printing to console, but this also
# means we won't get any logs from av, if they aren't FATAL or PANIC level.
av.logging.set_level(av.logging.FATAL)


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

    check_threads = []
    brute_threads = []
    screenshot_threads = []

    debugger.debug(f"Starting CheckerThreads")
    for _ in range(config.CHECK_THREADS):
        check_worker = CheckerThread(check_queue, brute_queue)
        check_worker.daemon = True
        check_worker.start()
        check_threads.append(check_worker)

    debugger.debug(f"Starting BruteThreads")
    for _ in range(config.BRUTE_THREADS):
        brute_worker = BruteThread(brute_queue, screenshot_queue)
        brute_worker.daemon = True
        brute_worker.start()
        brute_threads.append(brute_worker)

    debugger.debug(f"Starting ScreenshotThreads")
    for _ in range(config.SCREENSHOT_THREADS):
        screenshot_worker = ScreenshotThread(screenshot_queue)
        screenshot_worker.daemon = True
        screenshot_worker.start()
        screenshot_threads.append(screenshot_worker)

    logging.info(f"{Fore.GREEN}Starting...\n{Style.RESET_ALL}")

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
    config.DEBUG_LOG_FILE.rename(config.REPORT_FOLDER / config.DEBUG_LOG_FILE.name)
    screenshots = list(config.PICS_FOLDER.iterdir())
    logging.info(f"{Fore.GREEN}Saved {len(screenshots)} screenshots{Style.RESET_ALL}")
    logging.info(
        f"{Fore.GREEN}Report available at {str(config.REPORT_FOLDER)}{Style.RESET_ALL}"
    )

