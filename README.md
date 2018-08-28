# RTSPBrute

**Checks** RTSP IP streams, **brutes** them and **makes screenshots!**

## Installation:

1. `git clone https://gitlab.com/woolf/RTSPbrute.git` or download.
2. `pip install -r requirements.txt`

## Usage:

1. Scan IP ranges for RTSP stream or get them from Shodan/Censys etc.
2. Paste them in `hosts.txt`.
3. Run `python core.py` in your command line.

## Config:

In `config.py` you can specify number of threads.