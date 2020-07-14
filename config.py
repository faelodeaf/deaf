from tqdm import tqdm
from threading import Lock

from modules import *

# Number of threads to run CheckThread, BruteThread and ScreenshotThread:
CHECK_THREADS = 200
BRUTE_THREADS = 100
SCREENSHOT_THREADS = 50

LOCK = Lock()
PORT = 554
SOCKET_TIMEOUT = 10


DIRECTORIES = []
CREDENTIALS = []

ERROR_LIST = [
    "404 Not Found",
    "\x15\x00\x00\x00\x02\x02",
    "400",
    "401",
    "403",
    "451",
    "503",
]

with open("routes.txt") as file:
    for line in file:
        DIRECTORIES.append(line.strip(" \t\n\r"))

with open("credentials.txt") as file:
    for line in file:
        CREDENTIALS.append(line.strip(" \t\n\r"))


def create_bars():
    """
    Creates status bars from tqdm.
    """
    global check_bar
    global brute_bar
    global screenshot_bar

    check_bar = tqdm(total=0, desc="Total", position=0, ascii=True)
    brute_bar = tqdm(total=0, desc="Brute", position=1, ascii=True)
    screenshot_bar = tqdm(total=0, desc="Screen", position=2, ascii=True)


def update_bar(cls, main=False):
    """
    Updates TQDM status bar.

    Set main to true, if it's called from class that specifies on that task, for example: you finished checking ip and you need to update status bar, so you set main=True, otherwise it updates total number of tasks for next job.
    """
    global check_bar
    global brute_bar
    global screenshot_bar

    with LOCK:
        if cls == CheckerThread:
            if main:
                check_bar.update()
            else:
                brute_bar.total += 1
        if cls == BruteThread:
            if main:
                brute_bar.update()
            else:
                screenshot_bar.total += 1
        if cls == ScreenshotThread:
            screenshot_bar.update()
