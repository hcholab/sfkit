import json
import socket

from sfkit.sidecar.utils import get_sock_path


def client_command(study_id: str, data_path: str):
    sock_path = get_sock_path()
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_path)
    request = json.dumps({"study_id": study_id, "data_path": data_path})
    client.sendall(request.encode("utf-8"))

    while True:
        if data := client.recv(1024):
            print(data.decode("utf-8"))
        else:
            break
    client.close()
