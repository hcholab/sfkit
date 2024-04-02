import os

from sfkit.utils import constants


def get_sock_path():
    sock_path = constants.SOCK_PATH
    sock_dir = os.path.dirname(sock_path)
    if not os.path.exists(sock_dir):
        print(f"\nDirectory {sock_dir} does not exist. Please create it or set SFKIT_SOCK to a valid path\n")
        exit(1)
    return sock_path
