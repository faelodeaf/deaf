import collections
import logging
import threading
from queue import Queue
from typing import Callable, List

import av
from rich.panel import Panel

import config
from modules import utils, worker
from modules.cli.input import parser
from modules.cli.output import console
from modules.rtsp import RTSPClient


def start_threads(number: int, target: Callable, *args) -> List[threading.Thread]:
    debugger.debug(
        f"Starting {number} threads of {target.__module__}.{target.__name__}"
    )
    threads = []
    for _ in range(number):
        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        threads.append(thread)
        thread.start()
    return threads


def wait_for(queue: Queue, threads: List[threading.Thread]):
    """Waits for queue and then threads to finish."""
    queue.join()
    [queue.put(None) for _ in range(len(threads))]
    [t.join() for t in threads]


if __name__ == "__main__":
    args = parser.parse_args()

    # Logging module set up
    debugger = logging.getLogger("debugger")
    debugger.setLevel(logging.DEBUG)
    if args.debug:
        file_handler = logging.FileHandler(config.DEBUG_LOG_FILE, "w")
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(funcName)s] %(message)s"
            )
        )
        debugger.addHandler(file_handler)
    else:
        debugger.addHandler(logging.NullHandler())
    debugger.propagate = False

    # Redirect PyAV logs only to file
    libav_logger = logging.getLogger("libav")
    libav_logger.setLevel(logging.DEBUG)
    if args.debug:
        libav_logger.addHandler(file_handler)
    libav_logger.propagate = False
    av_logger = logging.getLogger("av")
    av_logger.setLevel(logging.DEBUG)
    if args.debug:
        av_logger.addHandler(file_handler)
    av_logger.propagate = False
    # This disables ValueError from av module printing to console, but this also
    # means we won't get any logs from av, if they aren't FATAL or PANIC level.
    av.logging.set_level(av.logging.FATAL)

    targets = collections.deque(set(utils.load_txt(args.targets, "targets")))
    config.ROUTES = utils.load_txt(args.routes, "routes")
    config.CREDENTIALS = utils.load_txt(args.credentials, "credentials")

    config.PORTS = args.ports

    utils.create_folder(config.PICS_FOLDER)
    utils.create_file(config.RESULT_FILE)
    utils.generate_html(config.HTML_FILE)

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    check_threads = start_threads(
        args.check_threads, worker.brute_routes, check_queue, brute_queue
    )
    brute_threads = start_threads(
        args.brute_threads, worker.brute_credentials, brute_queue, screenshot_queue
    )
    screenshot_threads = start_threads(
        args.screenshot_threads, worker.screenshot_targets, screenshot_queue
    )

    console.print("[green]Starting...\n")

    config.progress_bar.update(config.CHECK_PROGRESS, total=len(targets))
    config.progress_bar.start()
    while targets:
        check_queue.put(RTSPClient(ip=targets.popleft(), timeout=args.timeout))

    wait_for(check_queue, check_threads)
    debugger.debug("Check queue and threads finished")
    wait_for(brute_queue, brute_threads)
    debugger.debug("Brute queue and threads finished")
    wait_for(screenshot_queue, screenshot_threads)
    debugger.debug("Screenshot queue and threads finished")

    config.progress_bar.stop()

    print()
    if args.debug:
        file_handler.close()
        config.DEBUG_LOG_FILE.rename(config.REPORT_FOLDER / config.DEBUG_LOG_FILE.name)
    screenshots = list(config.PICS_FOLDER.iterdir())
    console.print(f"[green]Saved {len(screenshots)} screenshots")
    console.print(
        Panel(
            f"[bright_green]{str(config.REPORT_FOLDER)}", title="Report", expand=False
        ),
        justify="center",
    )
