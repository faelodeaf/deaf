import base64
import functools
import hashlib


@functools.lru_cache(maxsize=15)
def _basic_auth(credentials):
    encoded_cred = base64.b64encode(credentials.encode("ascii"))
    return f"Authorization: Basic {str(encoded_cred, 'utf-8')}"


def _digest_auth(option, ip, port, path, credentials, realm, nonce):
    username, password = credentials.split(":")
    uri = f"rtsp://{ip}:{port}{path}"
    HA1 = hashlib.md5(f"{username}:{realm}:{password}".encode("ascii")).hexdigest()
    HA2 = hashlib.md5(f"{option}:{uri}".encode("ascii")).hexdigest()
    response = hashlib.md5(f"{HA1}:{nonce}:{HA2}".encode("ascii")).hexdigest()
    return (
        "Authorization: Digest "
        f'username="{username}", '
        f'realm="{realm}", '
        f'nonce="{nonce}", '
        f'uri="{uri}", '
        f'response="{response}"'
    )


def describe(ip, port, path, credentials, realm=None, nonce=None):
    if credentials == ":":
        auth_str = ""
    elif realm:
        auth_str = _digest_auth("DESCRIBE", ip, port, path, credentials, realm, nonce)
    else:
        auth_str = _basic_auth(credentials)

    packet = (
        f"DESCRIBE rtsp://{ip}:{port}{path} RTSP/1.0\r\n"
        "CSeq: 2\r\n"
        f"{auth_str}"
        "User-Agent: Mozilla/5.0\r\n"
        "Accept: application/sdp\r\n"
        "\r\n"
    )
    return packet
