import json
import os
import socket
from threading import Thread

from sfkit.auth.auth import auth
from sfkit.auth.setup_networking import setup_networking
from sfkit.encryption.generate_personal_keys import generate_personal_keys
from sfkit.parser import get_parser
from sfkit.protocol.register_data import register_data
from sfkit.protocol.run_protocol import run_protocol


def server_command():
    sock_path = os.getenv("SFKIT_SOCK", "/home/jupyter/.config/sfkit/server.sock")
    if os.path.exists(sock_path):
        os.remove(sock_path)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    server.listen(1)

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

    while True:
        client, _ = server.accept()
        Thread(target=handle_client, args=(client,)).start()


def client_command(study_id: str, data_path: str):
    sock_path = os.getenv("SFKIT_SOCK", "/home/jupyter/.config/sfkit/server.sock")
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


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    if args.command == "server":
        server_command()
    elif args.command == "client":
        client_command(args.study_id, args.data_path)
    elif args.command == "auth":
        study_id: str = args.study_id or ""
        auth(study_id)
    elif args.command == "networking":
        ports = args.ports or ""
        ip_address = args.ip_address or ""
        setup_networking(ports, ip_address)
    elif args.command == "generate_keys":
        generate_personal_keys()
    elif args.command == "register_data":
        geno_binary_file_prefix = args.geno_binary_file_prefix or ""
        data_path = args.data_path or ""
        register_data(geno_binary_file_prefix, data_path)
    elif args.command == "run_protocol":
        phase: str = ""  # args.phase or ""
        demo: bool = args.demo or False
        visualize_results: str = args.visualize_results or ""
        results_path: str = args.results_path or ""
        retry: bool = args.retry or False
        skip_cp0: bool = args.skip_cp0 or False
        run_protocol(phase, demo, visualize_results, results_path, retry, skip_cp0)
    else:
        parser.print_help()
