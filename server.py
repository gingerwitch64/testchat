import threading
import socket
import socketserver
import sqlite3
import sys

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(1024), 'ascii')
        cur_thread = threading.current_thread()
        print(f"Replying to {} on {cur_thread}", 0)
        response = bytes(
                "{}: {}".format(cur_thread.name, data),
                'ascii'
                )
        self.request.sendall(response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main(arg = sys.argv):
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
