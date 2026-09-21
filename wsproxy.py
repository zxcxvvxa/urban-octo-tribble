import socket
import select
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

LISTEN_PORT = 2222
SSH_HOST = "127.0.0.1"
SSH_PORT = 22

class WSProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Accept requests to /cxlvin or any path passed by Nginx
        if self.path not in ["/cxlvin", "/", ""]:
            self.send_error(404, "Path Not Found")
            return

        try:
            target = socket.create_connection((SSH_HOST, SSH_PORT), timeout=10)
            target.setblocking(False)
        except Exception:
            self.send_error(502, "SSH service unreachable")
            return

        # Send HTTP 101 Switching Protocols response
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.end_headers()

        client_sock = self.connection
        client_sock.setblocking(False)

        sockets = [client_sock, target]

        try:
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, 30)
                if exceptional:
                    break
                if not readable:
                    continue
                for s in readable:
                    other = target if s is client_sock else client_sock
                    try:
                        data = s.recv(65536)
                        if not data:
                            return
                        other.sendall(data)
                    except (BlockingIOError, InterruptedError):
                        continue
                    except Exception:
                        return
        except Exception:
            pass
        finally:
            target.close()

    def log_message(self, format, *args):
        return

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    server = ThreadedHTTPServer(("0.0.0.0", LISTEN_PORT), WSProxyHandler)
    server.serve_forever()
