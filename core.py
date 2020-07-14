import ipaddress
from queue import Queue

import av

# Disables warnings
av.logging.set_level(av.logging.ERROR)

import config
from modules import *


def parse_input_line(input_line):
    """
    Parse input line, if it containts IP, return it.
    Supported inputs:
        1) 1.2.3.4
        2) 192.168.0.0/24
        3) 1.2.3.4 - 5.6.7.8
    Any non-ip value will be ignored.
    """

    ip_object = None
    try:
        # Input is in range form ("1.2.3.4 - 5.6.7.8"):
        if "-" in input_line:
            input_ips = input_line.split("-")
            ranges = [
                ipaddr
                for ipaddr in ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(input_ips[0]),
                    ipaddress.IPv4Address(input_ips[1]),
                )
            ]
            ip_object = ranges
        # Input is in CIDR form ("192.168.0.0/24"):
        elif "/" in input_line:
            network = ipaddress.ip_network(input_line)
            ip_object = network
        # Input is a single ip ("1.1.1.1"):
        else:
            ip = ipaddress.ip_address(input_line)
            ip_object = ip
    except ValueError:
        # If we get any non-ip value just ignore it
        pass

    # The object is just one ip, simply yield it:
    if isinstance(ip_object, ipaddress.IPv4Address):
        yield str(ip_object)
    # The object is a network, yield every host in it:
    else:
        for cidr in ip_object:
            for host in cidr.hosts():
                yield str(host)


if __name__ == "__main__":
    config.create_bars()

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    for _ in range(config.CHECK_THREADS):
        check_worker = CheckerThread(check_queue, brute_queue)
        check_worker.setDaemon(True)
        check_worker.start()

    for _ in range(config.BRUTE_THREADS):
        brute_worker = BruteThread(brute_queue, screenshot_queue)
        brute_worker.setDaemon(True)
        brute_worker.start()

    for _ in range(config.SCREENSHOT_THREADS):
        screenshoot_worker = ScreenshotThread(screenshot_queue)
        screenshoot_worker.setDaemon(True)
        screenshoot_worker.start()

    with open("hosts.txt") as file:
        for line in file:
            for ip in parse_input_line(line.strip(" \t\n\r")):
                check_queue.put(ip)
    config.check_bar.total = check_queue.qsize()

    check_queue.join()
    config.check_bar.close()

    brute_queue.join()
    config.brute_bar.close()

    screenshot_queue.join()
    config.screenshot_bar.close()
