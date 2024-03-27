import json
import os
import socket
import sys
from contextlib import contextmanager
from io import StringIO
from threading import Thread

from sfkit.auth.auth import auth
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption.generate_personal_keys import generate_personal_keys
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol
from sfkit.sidecar.utils import get_sock_path


@contextmanager
def capture_output():
    new_out = StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = new_out
        yield sys.stdout
    finally:
        sys.stdout = old_out


def handle_client(client):
    try:
        while True:
            data = client.recv(1024)
            if not data:
                break
            request = json.loads(data.decode("utf-8"))
            study_id = request.get("study_id", "")
            data_path = request.get("data_path", "")

            with capture_output() as output:
                auth(study_id)
            client.sendall(output.getvalue().encode("utf-8"))

            with capture_output() as output:
                setup_networking()
            client.sendall(output.getvalue().encode("utf-8"))

            with capture_output() as output:
                generate_personal_keys()
            client.sendall(output.getvalue().encode("utf-8"))

            with capture_output() as output:
                register_data(data_path=data_path)
            client.sendall(output.getvalue().encode("utf-8"))

            with capture_output() as output:
                run_protocol()
            client.sendall(output.getvalue().encode("utf-8"))

            response = f"All commands executed for study_id: {study_id}, data_path: {data_path}"
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
