import json
import os
import socket
import sys
import logging
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
def capture_output_and_logs():
    new_out = StringIO()
    new_err = StringIO()
    old_out = sys.stdout
    old_err = sys.stderr
    stream_handler = logging.StreamHandler(new_out)
    logger = logging.getLogger()
    old_handlers = logger.handlers[:]
    try:
        sys.stdout = new_out
        sys.stderr = new_err
        logger.handlers = [stream_handler]
        yield sys.stdout, sys.stderr, new_out
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        logger.handlers = old_handlers


def handle_client(client):
    try:
        while True:
            data = client.recv(1024)
            if not data:
                break
            request = json.loads(data.decode("utf-8"))
            study_id = request.get("study_id", "")
            data_path = request.get("data_path", "")

            def execute_and_send_feedback(operation):
                with capture_output_and_logs() as (stdout, stderr, logs):
                    operation()
                feedback = logs.getvalue() + stdout.getvalue() + stderr.getvalue()
                client.sendall(feedback.encode("utf-8"))

            execute_and_send_feedback(lambda: auth(study_id))
            execute_and_send_feedback(lambda: setup_networking())
            execute_and_send_feedback(lambda: generate_personal_keys())
            execute_and_send_feedback(lambda: register_data(data_path=data_path))
            execute_and_send_feedback(lambda: run_protocol())

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
