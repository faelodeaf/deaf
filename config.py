import time
from pathlib import Path
from typing import List

from modules.cli.output import progress_bar

ROUTES: List[str]
CREDENTIALS: List[str]
PORTS: List[int]

CHECK_PROGRESS = progress_bar.add_task("[bright_red]Checking...", total=0)
BRUTE_PROGRESS = progress_bar.add_task("[bright_yellow]Bruting...", total=0)
SCREENSHOT_PROGRESS = progress_bar.add_task("[bright_green]Screenshoting...", total=0)

start_datetime = time.strftime("%Y.%m.%d-%H.%M.%S")
DEBUG_LOG_FILE = Path.cwd() / "debug.log"
REPORT_FOLDER = Path.cwd() / "reports" / start_datetime
PICS_FOLDER = REPORT_FOLDER / "pics"
RESULT_FILE = REPORT_FOLDER / "result.txt"
HTML_FILE = REPORT_FOLDER / "index.html"
