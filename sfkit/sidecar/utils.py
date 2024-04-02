import os

from sfkit.utils import constants


def get_sock_path():
    sock_path = constants.SOCK_PATH
    sock_dir = os.path.dirname(sock_path)
    os.makedirs(sock_dir, mode=0o770, exist_ok=True)
    return sock_path
