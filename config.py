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
PICS_FOLDER = Path.cwd() / 'pics'
REPORTS_FOLDER = Path.cwd() / 'reports'
DEBUG_LOG_FILE = Path.cwd() / 'debug.log'
RESULT_FILE = Path.cwd() / 'result.txt'

ERROR_LIST = [
    "404 Not Found",
    "\x15\x00\x00\x00\x02\x02",
    "400",
    "451",
    "503",
]
