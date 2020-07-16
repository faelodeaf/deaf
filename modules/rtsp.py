import base64
import hashlib
import socket
import sys
from enum import Enum
from ipaddress import ip_address
from typing import List

sys.path.append("..")

import config


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
        self, ip: str, port: int = 554, credentials: str = "", timeout: int = 2
    ) -> None:
        try:
            ip_address(ip)
            self.ip = ip
        except ValueError as e:
            raise e

        if port not in range(0, 65536):
            raise ValueError(f"Port ({port}) passed to RTSPClient() is not valid")

        self.port = port
        self.credentials = credentials
        self.routes: List[str] = []
        self.timeout = timeout
        self.status: Status = Status.NONE
        self.auth_method: AuthMethod = AuthMethod.NONE
        self.realm: str = None
        self.nonce: str = None
        self.available: bool = False

        self._socket = socket.socket()
        self._packet = None
        self._data = None

    @property
    def route(self):
        if len(self.routes) > 0:
            return self.routes[0]
        else:
            return ""

    @property
    def route_found(self):
        return len(self.routes) > 0

    @property
    def credentials_found(self):
        return bool(self.credentials)

    def connect(self):
        self._socket.close()
        self._socket = socket.create_connection((self.ip, self.port), self.timeout)

    def create_packet(self, path="", credentials=""):
        """
        Creates describe packet, for example:

        DESCRIBE rtsp://admin:12345@127.0.0.1/webcam RTSP/1.0
        CSeq: 2
        Accept: application/sdp
        User-Agent: Mozilla/5.0

        """

        def _gen_auth_str(cred):
            if (
                self.auth_method is AuthMethod.NONE
                or self.auth_method is AuthMethod.BASIC
            ):
                encoded_cred = base64.b64encode(cred.encode("ascii"))
                auth_str = f"Authorization: Basic {str(encoded_cred, 'utf-8')}"
            else:
                username, password = cred.split(":")
                uri = f"rtsp://{self.ip}:{self.port}{path}"
                HA1 = hashlib.md5(
                    f"{username}:{self.realm}:{password}".encode("ascii")
                ).hexdigest()
                HA2 = hashlib.md5(f"DESCRIBE:{uri}".encode("ascii")).hexdigest()
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
            if cred:
                auth_str = _gen_auth_str(cred)
                packet += f"{auth_str}\r\n"
            packet += "User-Agent: Mozilla/5.0\r\n"
            packet += "Accept: application/sdp\r\n"
            packet += "\r\n"
            return packet

        if not path:
            path = self.route
        if not credentials:
            credentials = self.credentials
        self._packet = _gen_describe(path, credentials)

    def send_packet(self):
        """
        Sends packet to the opened connection and receives data back.
        """
        self._socket.sendall(self._packet.encode())
        self._data = repr(self._socket.recv(1024))

