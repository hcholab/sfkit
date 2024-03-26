import json
import os
import socket
from threading import Thread

from sfkit.sidecar.utils import get_sock_path


def handle_client(client):
    try:
        while True:
            data = client.recv(1024)
            if not data:
                break
            request = json.loads(data.decode("utf-8"))
            study_id = request.get("study_id", "")
            data_path = request.get("data_path", "")
            # Execute the sequence of commands here
            # For simplicity, this is just a placeholder
            response = f"Commands executed for study_id: {study_id}, data_path: {data_path}"
            client.sendall(response.encode("utf-8"))
    finally:
        client.close()


def server_command():
    sock_path = get_sock_path()
    if os.path.exists(sock_path):
        os.remove(sock_path)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    server.listen(1)

    while True:
        client, _ = server.accept()
        Thread(target=handle_client, args=(client,)).start()
