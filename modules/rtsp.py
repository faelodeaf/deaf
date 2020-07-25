import socket
import threading
from enum import Enum
from ipaddress import ip_address
from typing import List, Union

from modules.packet import describe


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
    __slots__ = (
        "ip",
        "port",
        "credentials",
        "routes",
        "timeout",
        "status",
        "auth_method",
        "realm",
        "nonce",
        "_local",
    )

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

    def create_packet(self, path=None, credentials=None):
        """Create describe packet."""

        if not path:
            path = self.route
        if not credentials:
            credentials = self.credentials

        self._local.packet = describe(
            self.ip, self.port, path, credentials, self.realm, self.nonce
        )

    def send_packet(self):
        """Send packet to the open connection and receive data back."""
        self.socket.sendall(self._local.packet.encode())
        self.data = repr(self.socket.recv(1024))

    @staticmethod
    def get_rtsp_url(
        ip: str, port: Union[str, int] = 554, credentials: str = ":", route: str = "/"
    ):
        """Return URL in RTSP format."""
        if credentials != ":":
            ip_prefix = f"{credentials}@"
        else:
            ip_prefix = ""
        return f"rtsp://{ip_prefix}{ip}:{port}{route}"

    def __str__(self) -> str:
        return self.get_rtsp_url(self.ip, self.port, self.credentials, self.route)
