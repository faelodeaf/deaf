# RTSPBrute

<p align="center">
   <a href="https://asciinema.org/a/351052?autoplay=1" target="_blank"><img src="https://asciinema.org/a/351052.svg" /></a>
</p>

> Inspired by [Cameradar](https://github.com/Ullaakut/cameradar)

## Features

- **Find accessible RTSP streams** on any target
- Brute-force **stream routes**
- Brute-force **credentials**
- **Make screenshots** on accessible streams
- Generate **user-friendly report** of the results:
  - `.txt` file with each found stream on new line
  - `.html` file with screenshot of each found stream

### Report files

- `result.txt`: Each target is on a new line. Import to VLC: change extension to `.m3u` and open in VLC
- `index.html`: Click on the screenshot to copy its link

## Installation

### Requirements

- `python` (> `3.7`)
- `av`
- `Pillow`
- `rich`

### Steps to install

1. `git clone https://gitlab.com/woolf/RTSPbrute.git`
2. `cd RTSPbrute`
3. `pip install -r requirements.txt`

## CLI

```
USAGE
    $ core.py [-h] [-t TARGETS] [-p PORTS [PORTS ...]] [-r ROUTES] [-c CREDENTIALS]
              [-ct N] [-bt N] [-st N] [-T TIMEOUT] [-d]

ARGUMENTS
    -h, --help                     show this help message and exit
    -t, --targets TARGETS          the targets on which to scan for open RTSP streams
    -p, --ports PORTS [PORTS ...]  the ports on which to search for RTSP streams
    -r, --routes ROUTES            the path on which to load a custom routes
    -c, --credentials CREDENTIALS  the path on which to load a custom credentials
    -ct, --check-threads N         the number of threads to brute-force the routes
    -bt, --brute-threads N         the number of threads to brute-force the credentials
    -st, --screenshot-threads N    the number of threads to screenshot the streams
    -T, --timeout TIMEOUT          the timeout to use for sockets
    -d, --debug                    enable the debug logs

EXAMPLES
    $ python core.py
    $ python core.py -t ips.txt -p 554 5554
    $ python core.py -r paths.txt -c combinations.txt
    $ python core.py -st 10 -T 10
```

- **"-t, --targets"** (`hosts.txt`): Set custom path to the input file. The file can contain IPs, IP ranges and CIDRs. Each one of them should be on a separate line, e.g.:

```
0.0.0.0
192.168.100.1-192.168.254.1
192.17.0.0/16
```

- **"-p, --ports"** (`554`): Set custom ports, e.g.: `-p 554 5554 8554`
- **"-r, --routes"** (`routes.txt`): Set custom path to the file with routes. Each route should start with `/` and be on a separate line, e.g.:

```
/1
/11
/h264
```

- **"-c, --credentials"** (`credentials.txt`): Set custom path to the file with credentials. Each combination should contain `:` and be on a separate line, e.g.:

```
admin:admin
user:user
```

- **"-ct, --check-threads"** (`500`): Set custom number of threads to brute-force the routes
- **"-bt, --brute-threads"** (`200`): Set custom number of threads to brute-force the credentials
- **"-st, --screenshot-threads"** (`20`): Set custom number of threads to screenshot the streams. Smaller number leads to more successful screenshots: when there's too much threads PyAV will throw errors and wouldn't connect to target.
- **"-T, --timeout"** (`2`): Set custom timeout value for socket connections
- **"-d, --debug"** (`False`): Enable debug logging to `debug.log` file

## TODO

- [x] Add support for multiple ports
- [ ] Optimize for large input
- [ ] Add tests
- [x] Add CLI
- [x] Beautify format of output to terminal
- [ ] Release on PyPI
