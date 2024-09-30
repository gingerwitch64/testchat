import json
import threading
import socket
import socketserver
import sqlite3
import sys

dbcon = sqlite3.connect("server.db")
dbcur = dbcon.cursor()


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = json.loads(str(self.request.recv(1024), 'utf-8'))
        response = {}
        match data["type"]:
            case "REG" | "REGISTER":
                if dbcur.execute(
                        "SELECT UserName FROM users WHERE UserName='?'", data["username"]
                        ).fetchone() is None:
                    response = {
                        "type": ""
                    }
            case "MSG" | "MESSAGE":
                response = "PLACEHOLDER"
            case "GET" | "FETCH":
                response = "PLACEHOLDER"
        cur_thread = threading.current_thread()
        print(f"Replying on {cur_thread}")
        self.request.sendall(bytes(response, 'utf-8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main(arg = sys.argv):
    dbcur.execute("CREATE TABLE messages ( Timestamp int, UserName varchar(255), Content varchar(255) )")
    dbcur.execute("CREATE TABLE users ( UserID int, UserName varchar(255) )")
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
