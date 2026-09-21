import socket
import select
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import threading

LISTEN_PORT = 2222
SSH_HOST = "127.0.0.1"
SSH_PORT = 22

class WSProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Establish TCP connection to OpenSSH
        try:
            target = socket.create_connection((SSH_HOST, SSH_PORT))
        except Exception:
            self.send_error(502, "SSH service unreachable")
            return

        # Complete WebSocket Handshake
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.end_headers()

        # Tunnel raw TCP streams bi-directionally
        client_sock = self.connection
        sockets = [client_sock, target]
        
        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 60)
                if not readable:
                    break
                for s in readable:
                    data = s.recv(8192)
                    if not data:
                        return
                    if s is client_sock:
                        target.sendall(data)
                    else:
                        client_sock.sendall(data)
        except Exception:
            pass
        finally:
            target.close()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    server = ThreadedHTTPServer(("127.0.0.1", LISTEN_PORT), WSProxyHandler)
    server.serve_forever()
