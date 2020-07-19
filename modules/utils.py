import ipaddress
import logging
import re
import sys
import threading
from pathlib import Path
from typing import List

from modules.rtsp import AuthMethod, RTSPClient

logger = logging.getLogger("debugger")

global_lock = threading.Lock()


def generate_html(path: Path):
    html_head = """<!DOCTYPE html><html><head><style>    
html{background-color: #141414}
img{cursor: pointer;border: 2px solid #707070;}
img:hover {border: 2px solid #8c8c8c;}
div.gallery img {width: 100%;height: auto;}
*{box-sizing: border-box;}
.responsive {padding: 6px 6px;float: left;width: 25%;}
@media only screen and (max-width: 700px){.responsive {width: 50%;margin: 1px 0;}}
@media only screen and (max-width: 500px){.responsive {width: 100%;}}
</style></head><body>\n"""
    html_script = """\n<script>function f(img){
var text = img.alt;
navigator.clipboard.writeText(text);}</script>"""
    logger.debug(f"Generating {path}")
    with path.open("w") as f:
        f.write(html_head)
        f.write("\n")
        f.write(html_script)
        f.write("</body></html>")


def create_folder(path: Path):
    logger.debug(f"Creating {path}")
    path.mkdir(parents=True)


def create_file(path: Path):
    logger.debug(f"Creating {path}")
    path.open("w", encoding="utf-8")


def append_result(result_file: Path, html_file: Path, pic_file: Path, rtsp: RTSPClient):
    with global_lock:
        # Append to .txt result file
        with result_file.open("a") as f:
            f.write(f"{get_camera_rtsp_url(rtsp)}\n")

        # Insert to .html gallery file
        if not pic_file.exists():
            return
        with html_file.open("r") as f:
            data = f.readlines()
        html_pic = f"""
<div class="responsive"><div class="gallery">
<img src="{pic_file.parent.name}/{pic_file.name}" alt="{get_camera_rtsp_url(rtsp)}" width="600" height="400" onclick="f(this)"></div></div>
        """
        data.insert(-4, html_pic)
        with html_file.open("w") as f:
            f.writelines(data)


def escape_chars(s: str):
    # Escape every character that's not a letter,
    # '_', '-', '.' or space with an '_'.
    return re.sub(r"[^\w-_. ]", "_", s)


def detect_code(data: str):
    return int(data[11:14])


def detect_auth_method(target):
    def _find_var(data, var):
        start = data.find(var)
        begin = data.find('"', start) + 1
        end = data.find('"', begin)
        if "Login to " in data[begin:end]:
            logger.debug(f"{get_camera_rtsp_url(target)} has LOGIN TO")
        return data[begin:end].lstrip("Login to ")

    data = str(target._data)

    if "Basic" in data:
        auth_method = "basic"
        target.auth_method = AuthMethod.BASIC
    elif "Digest" in data:
        auth_method = "digest"
        target.auth_method = AuthMethod.DIGEST
        target.realm = _find_var(data, "realm")
        target.nonce = _find_var(data, "nonce")
    else:
        auth_method = "no"
        target.auth_method = AuthMethod.NONE

    logger.debug(
        f"Stream {get_camera_rtsp_url(target)} uses {auth_method} authentication method\n"
    )


def get_camera_rtsp_url(rtsp_client):
    return f"rtsp://{rtsp_client.credentials}@{rtsp_client.ip}:{rtsp_client.port}{rtsp_client.route}"


def load_txt(path: str, name: str) -> List[str]:
    result = []
    try:
        if name == "credentials":
            result = [line.strip("\t\r") for line in get_lines(path)]
        if name == "routes":
            result = get_lines(path)
        if name == "targets":
            result = [
                target for line in get_lines(path) for target in parse_input_line(line)
            ]
    except FileNotFoundError as e:
        logging.error(f"Couldn't read {name} file at {path}: {str(e)}")
        sys.exit()
    logging.info(f"Loaded {len(result)} {name} from {path}")
    return result


def get_lines(path: str) -> List[str]:
    p = Path(path)
    lines = p.read_text().splitlines()
    return lines


def parse_input_line(input_line: str) -> List[str]:
    """
    Parse input line and return list with IPs.
    Supported inputs:
        1) 1.2.3.4
        2) 192.168.0.0/24
        3) 1.2.3.4 - 5.6.7.8
    Any non-ip value will be ignored.
    """
    try:
        # Input is in range form ("1.2.3.4 - 5.6.7.8"):
        if "-" in input_line:
            input_ips = input_line.split("-")
            ranges = [
                ipaddr
                for ipaddr in ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(input_ips[0].strip()),
                    ipaddress.IPv4Address(input_ips[1].strip()),
                )
            ]
            return [str(ip) for r in ranges for ip in r]

        # Input is in CIDR form ("192.168.0.0/24"):
        elif "/" in input_line:
            network = ipaddress.ip_network(input_line)
            return [str(ip) for ip in network]

        # Input is a single ip ("1.1.1.1"):
        else:
            ip = ipaddress.ip_address(input_line)
            return [str(ip)]
    except ValueError:
        # If we get any non-ip value just ignore it
        return []
