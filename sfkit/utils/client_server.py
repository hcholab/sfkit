import socket
import json
from sfkit.auth.auth import auth

from sfkit.protocol.run_protocol import run_protocol

PORT = 12345 

def send_command_to_server(command, *args):
    s = socket.socket()
    s.connect(('127.0.0.1', PORT))

    data = {
        'command': command,
        'args': args
    }

    s.send(json.dumps(data).encode())
    s.close()
    

def start_server():
    s = socket.socket()
    s.bind(('', PORT))
    s.listen(5)
    
    auth() 

    while True:
        c, addr = s.accept()

        data = c.recv(1024).decode()
        data = json.loads(data)

        command = data['command']
        args = data['args']
        execute_command(command, *args)

        c.close()

def execute_command(command, *args):
    if command == "run_protocol":
        run_protocol(*args)
