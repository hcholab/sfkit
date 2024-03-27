import os


def get_sock_path():
    sock_path = os.getenv("SFKIT_SOCK", "/home/jupyter/.config/sfkit/server.sock")
    sock_dir = os.path.dirname(sock_path)
    if not os.path.exists(sock_dir):
        print(f"\nDirecotry {sock_dir} does not exist. Please create it or set SFKIT_SOCK to a valid path\n")
        exit(1)
    return sock_path
