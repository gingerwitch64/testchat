import socket
import json
from uuid import uuid4

class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = None
        self.username = None
        self.uuid = None

        self.connect()
        self.register()

    # Connects client to socket, returns error code
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((self.ip, self.port))
            print(f"Connected to {self.ip}:{self.port}")
            return 0
        
        except ConnectionError as e:
            print(f"Failed to connect: {e}")
            return 1
        
    # Registers user into db, returns error code
    def register(self, username):
        if self.socket is None: 
            print("Client not connected to socket")
            return 1
        uuid = uuid4().hex

        data = {
            "type": "REGISTER",
            "username": username,
            "userid":uuid
        }

        try:
            self.socket.sendall(bytes(json.dumps(data), 'utf-8'))
            response = json.loads(str(self.socket.recv(1024), 'utf-8'))

        except Exception as e:
            print(f"Failed to send: {e}")
            return 1

        if response["status"] == 1:
            print("Registration failed")
            return 1
        
        self.username = username
        self.uuid = uuid
        return 0

    # Sends message to server, returns error code
    def send(self, message):
        if self.socket is None: 
            print("Client not connected to socket")
            return 1
        
        data = {
            "type": "MESSAGE",
            "userid": self.uuid,
            "text": message
        }

        try:
            self.socket.sendall(bytes(json.dumps(data), 'utf-8'))
            response = json.loads(str(self.socket.recv(1024), 'utf-8'))

        except Exception as e:
            print(f"Failed to send: {e}")
            return 1

        return 0
    
    # Returns -1 if fetch request failed, else returns messages
    # Unsure of whether this function is private
    def _fetch(self, since=None, last=None): 
        if self.socket is None: 
            print("Client not connected to socket")
            return -1
        
        data = {
            "type": "FETCH",
            "since": since,
            "last": last
        }

        try:
            self.socket.sendall(bytes(json.dumps(data), 'utf-8'))
            response = json.loads(str(self.socket.recv(1024), 'utf-8'))

        except Exception as e:
            print(f"Failed to send: {e}")
            return -1

        if response['status'] == 0:
            print("Fetch request failed")
            return -1

        return response['messages']

    # Closes socket connection, returns error code
    def close(self):
        if self.socket is None:
            print("Client not connected to socket")
            return 1
        
        self.socket.close()
        self.socket = None
        print(f"Closed connection")
        return 0
        
