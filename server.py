import json
import os.path
import threading
import socket
import socketserver
import sqlite3
import time

# Autocommit is enabled due to the proof-of-concept nature of this project
SQLITE_FILEPATH = "server.db"
SQLITE_AUTOCOMMIT = True

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print(f"Request recieved from: {self.client_address}")
        dbcon = sqlite3.connect(SQLITE_FILEPATH, autocommit=SQLITE_AUTOCOMMIT)
        dbcur = dbcon.cursor()
        
        data = json.loads(str(self.request.recv(1024), 'utf-8'))
        response = {}

        match data["type"]:

            case "REG" | "REGISTER":
                userTaken = not ((dbcur.execute("SELECT UserName FROM users WHERE UserName=?", (data["username"],)).fetchone() is None)
                             and (dbcur.execute("SELECT UserName FROM users WHERE UserID=?",   (data["userid"],  )).fetchone() is None))
                if not userTaken:
                    dbcur.execute("INSERT INTO users VALUES (?, ?)", (data["userid"], data["username"],))
                    print(f"Registered new user: {data["username"]}")
                else:
                    print(f"Failed to register new user: {data["username"]}")
                response = {
                    "type": "REG",
                    "status": (userTaken * 1), # convert the result bool into an integer status code
                }

            case "MSG" | "MESSAGE":
                username = dbcur.execute("SELECT UserName FROM users WHERE UserID=?", (data["userid"],)).fetchone()
                useridDNE = username is None # UserID Does Not Exist?
                if not useridDNE:
                    username = username[0]
                    timestamp = int(time.time())
                    dbcur.execute("INSERT INTO messages VALUES (?, ?, ?)", (timestamp, username, data["text"],))
                    print(f"{timestamp} {username}: '{data["text"]}'")
                else:
                    print("MESSAGE failed, UserID is not linked to a UserName.")
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
                    response["messages"] = dbcur.execute("SELECT * FROM messages WHERE Timestamp >= ?", (data["since"],)).fetchall()
                elif "last" in data:
                    response["messages"] = dbcur.execute("SELECT * FROM messages ORDER BY Timestamp DESC LIMIT ?", (int(data["last"]),)).fetchall()
                else:
                    response["messages"] = dbcur.execute("SELECT * FROM messages ORDER BY Timestamp DESC LIMIT 1").fetchall()

        cur_thread = threading.current_thread()
        print(f"Replying to {response["type"]} on {cur_thread}")
        self.request.sendall(bytes(json.dumps(response), 'utf-8'))
        dbcon.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main(host="localhost",port=5500):
    if not os.path.isfile(SQLITE_FILEPATH):
        print( "Database file does not exist...\n",
              f"Setting up \'{SQLITE_FILEPATH}\' now...\n",
              f"Autocommit is {SQLITE_AUTOCOMMIT}\n")
        dbcon = sqlite3.connect(SQLITE_FILEPATH, autocommit=SQLITE_AUTOCOMMIT)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE messages ( Timestamp int, UserName varchar(255), Content varchar(255) )")
        dbcur.execute("CREATE TABLE users ( UserID char(32), UserName varchar(255) )")
        dbcon.close()

    server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
    with server: 
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"Server loop running in thread: {server_thread.name}")
        
        shutoff = False
        while not shutoff:
            prompt = input("Awaiting next prompt...\n")
            if prompt in ["q", "quit", "exit", "stop", "shutdown"]:
                print("Shutting down server...")
                shutoff = True

        server.shutdown()

if __name__ == "__main__":
    main()
