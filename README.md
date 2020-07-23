# RTSPBrute

<p align="center">
   <a href="https://asciinema.org/a/348924?autoplay=1" target="_blank"><img src="https://asciinema.org/a/348924.svg" /></a>
</p>

> Inspired by [Cameradar](https://github.com/Ullaakut/cameradar)


## Features

* **Find accessible RTSP streams** on any target
* Brute-force **stream routes**
* Brute-force **credentials**
* **Make screenshots** on accessible streams
* Generate **user-friendly report** of the results:
    * `.txt` file with each found stream on new line
    * `.html` file with screenshot of each found stream

### Report files

#### `result.txt`

* Each target is on a new line
* Import to VLC: change extension to `.m3u` and open in VLC

#### `index.html`

* Responsive
* Click on the screenshot to copy its link


## Installation

### Requirements

* `python` (> `3.7`)
* `av`
* `colorama`
* `Pillow`

### Steps to install

1. `git clone https://gitlab.com/woolf/RTSPbrute.git`
2. `cd RTSPbrute`
3. `pip install -r requirements.txt`


## Configuration

At the moment it is possible to change only the following variables in `config.py` file:
* Number of `CHECK`, `BRUTE` and `SCREENSHOT` `_THREADS`
* `PORT` to check
* `SOCKET_TIMEOUT`

In the future, the CLI will be used for this.


## Usage

1. Get IPs in any format (`1.1.1.1-1.10.10.1`, `192.168.100.1/24`, `8.8.8.8`):
    * Scan manually
    * Use [Shodan](https://www.shodan.io/) or [Censys](https://censys.io/)
2. Insert them into the `hosts.txt` file so that each IP object (range, cidr or single IP) is on a new line
3. `python core.py`


## TODO

- [ ] Add support for multiple ports
- [ ] Add tests
- [ ] Add CLI
- [ ] Beautify format of output to terminal
- [ ] Release on PyPI