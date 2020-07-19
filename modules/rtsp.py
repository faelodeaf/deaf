import base64
import hashlib
import socket
import threading
from enum import Enum
from ipaddress import ip_address
from typing import List, Union


class AuthMethod(Enum):
    NONE = 0
    BASIC = 1
    DIGEST = 2


class Status(Enum):
    CONNECTED = 0
    TIMEOUT = 1
    BLOCKED = 2
    UNIDENTIFIED = 100
    NONE = -1


class RTSPClient:
    def __init__(
        self, ip: str, port: int = 554, credentials: str = ":", timeout: int = 2
    ) -> None:
        try:
            ip_address(ip)
        except ValueError as e:
            raise e

        if port not in range(0, 65536):
            raise ValueError(f"({port}) isn't valid port")

        self.ip = ip
        self.port = port
        self.credentials = credentials
        self.routes: List[str] = []
        self.timeout = timeout
        self.status: Status = Status.NONE
        self.auth_method: AuthMethod = AuthMethod.NONE
        self.realm: str = None
        self.nonce: str = None

        self._local = threading.local()

    @property
    def route(self):
        if len(self.routes) > 0:
            return self.routes[0]
        else:
            return ""

    @property
    def data(self):
        _data = getattr(self._local, "data", "")
        return _data

    @data.setter
    def data(self, value):
        self._local.data = value

    @data.deleter
    def data(self):
        del self._local.data

    @property
    def socket(self):
        _socket = getattr(self._local, "socket", None)
        return _socket

    @socket.setter
    def socket(self, value):
        self._local.socket = value

    @socket.deleter
    def socket(self):
        del self._local.socket

    def connect(self):
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.ip, self.port))

    def create_packet(self, path="", credentials=""):
        """Create describe packet."""

        def _gen_auth_str(cred, option):
            if self.auth_method is AuthMethod.BASIC:
                encoded_cred = base64.b64encode(cred.encode("ascii"))
                auth_str = f"Authorization: Basic {str(encoded_cred, 'utf-8')}"
            else:
                username, password = cred.split(":")
                uri = f"rtsp://{self.ip}:{self.port}{path}"
                HA1 = hashlib.md5(
                    f"{username}:{self.realm}:{password}".encode("ascii")
                ).hexdigest()
                HA2 = hashlib.md5(f"{option}:{uri}".encode("ascii")).hexdigest()
                response = hashlib.md5(
                    f"{HA1}:{self.nonce}:{HA2}".encode("ascii")
                ).hexdigest()
                auth_str = f"Authorization: Digest "
                auth_str += f'username="{username}", '
                auth_str += f'realm="{self.realm}", '
                auth_str += f'nonce="{self.nonce}", '
                auth_str += f'uri="{uri}", '
                auth_str += f'response="{response}"'
            return auth_str

        def _gen_describe(path, cred):
            packet = f"DESCRIBE rtsp://{self.ip}:{self.port}{path} RTSP/1.0\r\n"
            packet += "CSeq: 2\r\n"
            if cred and not self.auth_method is AuthMethod.NONE:
                auth_str = _gen_auth_str(cred, "DESCRIBE")
                packet += f"{auth_str}\r\n"
            packet += "User-Agent: Mozilla/5.0\r\n"
            packet += "Accept: application/sdp\r\n"
            packet += "\r\n"
            return packet

        if not path:
            path = self.route
        if not credentials:
            credentials = self.credentials

        self._local.packet = _gen_describe(path, credentials)

    def send_packet(self):
        """Send packet to the open connection and receive data back."""
        self.socket.sendall(self._local.packet.encode())
        self.data = repr(self.socket.recv(1024))

    @staticmethod
    def get_rtsp_url(
        ip: str, port: Union[str, int] = 554, credentials: str = ":", route: str = "/"
    ):
        """Return URL in RTSP format."""
        return f"rtsp://{credentials}@{ip}:{port}{route}"

    def __str__(self) -> str:
        return self.get_rtsp_url(self.ip, self.port, self.credentials, self.route)
