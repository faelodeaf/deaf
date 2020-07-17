import time
from pathlib import Path
from typing import List

CHECK_THREADS: int = 500
BRUTE_THREADS: int = 200
SCREENSHOT_THREADS: int = 50

PORT: int = 554
SOCKET_TIMEOUT: int = 2


CREDENTIALS: List[str] = []
ROUTES: List[str] = []
TARGETS: List[str] = []


start_datetime = time.strftime("%Y.%m.%d-%H.%M.%S")
DEBUG_LOG_FILE = Path.cwd() / 'debug.log'
REPORT_FOLDER = Path.cwd() / 'reports' / start_datetime
PICS_FOLDER = REPORT_FOLDER / 'pics'
RESULT_FILE = REPORT_FOLDER / 'result.txt'
HTML_FILE = REPORT_FOLDER / 'index.html'
