import json
import threading
import socket
import socketserver
import sqlite3
import sys

# Autocommit is enabled due to the proof-of-concept nature of this project
dbcon = sqlite3.connect("server.db", autocommit=True)
dbcur = dbcon.cursor()


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = json.loads(str(self.request.recv(1024), 'utf-8'))
        response = {}
        match data["type"]:
            case "REG" | "REGISTER":
                usernameAvailable = (dbcur.execute("SELECT UserName FROM users WHERE UserName='?'", (data["username"],)).fetchone() is None)
                userIDAvailable   = (dbcur.execute("SELECT UserName FROM users WHERE UserID='?'",   (data["userid"],  )).fetchone() is None)
                if usernameAvailable and userIDAvailable:
                    response = {
                        "type": "REG",
                        "status": 0,
                    }
                else:
                    # No matter what, an error code must be sent for either a duplicate UserName OR UserID
                    # as letting a client know if a UserID is used can be exploited
                    response = {
                        "type": "REG",
                        "status": 1,
                    }
            case "MSG" | "MESSAGE":
                # TODO: Insert message into messages table, only send status 0 on success
                response = {
                    "type": "MSG",
                    "status": 0,
                }
            case "GET" | "FETCH":
                response = "PLACEHOLDER"
        cur_thread = threading.current_thread()
        print(f"Replying on {cur_thread}")
        self.request.sendall(bytes(json.dumps(response), 'utf-8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main(arg = sys.argv):
    dbcur.execute("CREATE TABLE messages ( Timestamp int, UserName varchar(255), Content varchar(255) )")
    dbcur.execute("CREATE TABLE users ( UserID char(32), UserName varchar(255) )")
    HOST, PORT = "localhost", 0
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address 
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        server.shutdown()
  

if __name__ == "__main__":
    main()
