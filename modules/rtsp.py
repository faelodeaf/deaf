import socket
from ipaddress import ip_address

import sys
sys.path.append('..')

import config


class RTSPClient():
    """
    Implements basic interface for connecting to RTSP stream.

    Usage:
    >>> with RTSPClient('127.0.0.1') as client:
            client.create_packet('/webcam', 'admin:12345')
            client.send_packet()

    """

    def __init__(self, ip, port=554, credentials='', path=None, timeout=5):
        try:
            ip_address(ip)
            self.ip = ip
        except ValueError as e:
            raise e

        if port not in range(0, 65536):
            raise ValueError(
                f'Port ({port}) passed to RTSPClient() is not valid)')

        self.port = port
        self.credentials = credentials
        self.path = path
        self.timeout = timeout
        self.is_connected = None
        self._packet = None
        self._socket = None
        self._data = None

    def create_packet(self, path, credentials=''):
        """
        Creates describe packet, for example:

        DESCRIBE rtsp://admin:12345@127.0.0.1/webcam RTSP/1.0
        CSeq: 2
        Accept: application/sdp
        User-Agent: Mozilla/5.0

        """
        self.credentials = credentials
        self.path = path
        self._packet = (f'DESCRIBE rtsp://{self.credentials}@{self.ip}{path} RTSP/1.0\r\n'
                        + 'CSeq: 2\r\n'
                        + 'Accept: application/sdp\r\n'
                        + 'User-Agent: Mozilla/5.0\r\n\r\n')

    def send_packet(self):
        """
        Sends packet to the opened connection and receives data back.
        """
        self._socket.sendall(self._packet.encode())
        self._data = repr(self._socket.recv(1024))

    def is_available(self):
        """
        Checks if data doesn't contain errors.
        Useful for brute forcing directories.
        """
        if self._data:
            if all(error not in self._data for error in config.ERROR_LIST):
                return True
            else:
                return False
        else:
            return False

    def is_authorized(self):
        """
        Checks if data contains '200 OK', basically that means you're authorized.
        Useful for credentials brute forcing.
        """
        if self._data:
            if '200 OK' in self._data:
                return True
            else:
                return False
        else:
            return False

    def __enter__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.timeout)
        try:
            self._socket.connect((self.ip, self.port))
            self.is_connected = True
            return self
        except (socket.timeout, socket.error) as e:
            self.is_connected = False
            return None
        except Exception as e:
            self.is_connected = False
            return None

    def __exit__(self, *args):
        self._socket.close()
        return True
