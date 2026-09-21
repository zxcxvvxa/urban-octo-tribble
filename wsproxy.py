import socket
import select
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 2222
SSH_HOST = '127.0.0.1'
SSH_PORT = 22
BUFFER_SIZE = 65536

class WSProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Suppress default HTTP logging for performance

    def do_GET(self):
        # Respond to WebSocket Handshake
        self.send_response(101, 'Switching Protocols')
        self.send_header('Upgrade', 'websocket')
        self.send_header('Connection', 'Upgrade')
        self.end_headers()

        # Connect directly to SSH Daemon
        try:
            ssh_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssh_sock.connect((SSH_HOST, SSH_PORT))
            ssh_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            client_sock = self.connection
            client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Bidirectional zero-buffer pipe
            sockets = [client_sock, ssh_sock]
            while True:
                readable, _, errors = select.select(sockets, [], sockets, 60)
                if errors or not readable:
                    break
                for s in readable:
                    other = ssh_sock if s is client_sock else client_sock
                    data = s.recv(BUFFER_SIZE)
                    if not data:
                        return
                    other.sendall(data)
        except Exception:
            pass
        finally:
            ssh_sock.close()

def run_server():
    server = HTTPServer((LISTEN_HOST, LISTEN_PORT), WSProxyHandler)
    server.serve_forever()

if __name__ == '__main__':
    run_server()
