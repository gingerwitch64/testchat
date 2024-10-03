import json
import threading
import socket
import socketserver
import sqlite3
import time

# Autocommit is enabled due to the proof-of-concept nature of this project
dbcon = sqlite3.connect("server.db", autocommit=True)
dbcur = dbcon.cursor()


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = json.loads(str(self.request.recv(1024), 'utf-8'))
        response = {}
        match data["type"]:
            case "REG" | "REGISTER":
                userTaken = not ((dbcur.execute("SELECT UserName FROM users WHERE UserName='?'", (data["username"],)).fetchone() is None)
                             and (dbcur.execute("SELECT UserName FROM users WHERE UserID='?'",   (data["userid"],  )).fetchone() is None))
                if not userTaken:
                    dbcur.execute("INSERT INTO users VALUES (?, ?)", (data["userid"], data["username"],))
                response = {
                    "type": "REG",
                    "status": (userTaken * 1), # convert the result bool into an integer status code
                }
            case "MSG" | "MESSAGE":
                username = dbcur.execute("SELECT UserName FROM users WHERE UserID='?'", (data["userid"],)).fetchone()
                useridDNE = username is None
                if not useridDNE:
                    username = username[0]
                    dbcur.execute("INSERT INTO messages VALUES (?, ?, ?)", (int(time.time()), username, data["text"],))
                response = {
                    "type": "MSG",
                    "status": (useridDNE * 1), # if the userid returned no username, return an error
                }
            case "GET" | "FETCH":
                response = {
                    "type": "GET",
                    "messages": [],
                    "status": 0,
                }
                if "since" in data:
                    response["messages"] = dbcur.execute("SELECT * FROM messages WHERE Timestamp >= ?", data["since"]).fetchall()
                elif "last" in data:
                    response["messages"] = dbcur.execute("SELECT * FROM messages ORDER BY Timestamp DESC LIMIT ?", int(data["last"])).fetchall()
                else:
                    response["messages"] = dbcur.execute("SELECT * FROM messages ORDER BY Timestamp DESC LIMIT 1").fetchone()

        cur_thread = threading.current_thread()
        print(f"Replying on {cur_thread}")
        self.request.sendall(bytes(json.dumps(response), 'utf-8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main(host="localhost",port=5500):
    dbcur.execute("CREATE TABLE messages ( Timestamp int, UserName varchar(255), Content varchar(255) )")
    dbcur.execute("CREATE TABLE users ( UserID char(32), UserName varchar(255) )")
    server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
    with server: 
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        server.shutdown()
  

if __name__ == "__main__":
    main()
