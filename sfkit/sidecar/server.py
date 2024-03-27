import json
import os
import select
import socket
import subprocess
from threading import Thread

from sfkit.sidecar.utils import get_sock_path


def handle_client(client: socket.socket):
    try:
        while True:
            data = client.recv(1024)
            if not data:
                break
            request = json.loads(data.decode("utf-8"))
            study_id = request.get("study_id", "")
            data_path = request.get("data_path", "")

            client.sendall("Received request".encode("utf-8"))

            # Example of running a command and capturing its output
            process = subprocess.Popen(
                ["stdbuf", "-oL", "-eL", "sfkit", "all"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )  # TODO: add study_id and data_path args

            while process.poll() is None:
                rlist, _, _ = select.select([process.stdout, process.stderr], [], [])

                if not rlist:
                    process.kill()

                for stream in rlist:
                    line = stream.readline().strip()
                    print(line)
                    client.sendall(line.encode("utf-8"))

            process.wait()
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
