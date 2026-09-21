import socket
import select
import hashlib
import base64
import struct
import threading

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 2222
SSH_HOST = '127.0.0.1'
SSH_PORT = 22
BUFFER_SIZE = 65536
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def create_ws_frame(payload, opcode=0x2):
    length = len(payload)
    if length <= 125:
        header = struct.pack("!BB", 0x80 | opcode, length)
    elif length <= 65535:
        header = struct.pack("!BBH", 0x80 | opcode, 126, length)
    else:
        header = struct.pack("!BBQ", 0x80 | opcode, 127, length)
    return header + payload

def parse_ws_frame(buffer):
    if len(buffer) < 2:
        return None, None, buffer
    
    first_byte = buffer[0]
    second_byte = buffer[1]
    
    opcode = first_byte & 0x0F
    masked = (second_byte & 0x80) != 0
    payload_len = second_byte & 0x7F
    
    offset = 2
    if payload_len == 126:
        if len(buffer) < 4:
            return None, None, buffer
        payload_len = struct.unpack("!H", buffer[2:4])[0]
        offset = 4
    elif payload_len == 127:
        if len(buffer) < 10:
            return None, None, buffer
        payload_len = struct.unpack("!Q", buffer[2:10])[0]
        offset = 10
        
    mask_key = None
    if masked:
        if len(buffer) < offset + 4:
            return None, None, buffer
        mask_key = buffer[offset:offset+4]
        offset += 4
        
    if len(buffer) < offset + payload_len:
        return None, None, buffer
        
    data = buffer[offset:offset+payload_len]
    remaining = buffer[offset+payload_len:]
    
    if masked and mask_key:
        unmasked = bytearray(payload_len)
        for i in range(payload_len):
            unmasked[i] = data[i] ^ mask_key[i % 4]
        data = bytes(unmasked)
        
    return opcode, data, remaining

def handle_client(client_sock):
    client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    ssh_sock = None
    
    try:
        request_data = b""
        client_sock.settimeout(10.0)
        while b"\r\n\r\n" not in request_data:
            chunk = client_sock.recv(4096)
            if not chunk:
                client_sock.close()
                return
            request_data += chunk
        client_sock.settimeout(None)

        # Parse HTTP Headers cleanly in binary
        headers = {}
        lines = request_data.split(b"\r\n")
        for line in lines[1:]:
            if b":" in line:
                k, v = line.split(b":", 1)
                headers[k.strip().lower().decode('utf-8', errors='ignore')] = v.strip().decode('utf-8', errors='ignore')

        ws_key = headers.get("sec-websocket-key")
        
        # 1. Handshake response
        if ws_key:
            accept_key = base64.b64encode(hashlib.sha1((ws_key + GUID).encode('utf-8')).digest()).decode('utf-8')
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            client_sock.sendall(response.encode('utf-8'))
            is_ws = True
        else:
            response = (
                "HTTP/1.1 101 Connection Established\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n\r\n"
            )
            client_sock.sendall(response.encode('utf-8'))
            is_ws = False

        # 2. Connect to local SSH target
        ssh_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssh_sock.connect((SSH_HOST, SSH_PORT))
        ssh_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    except Exception:
        client_sock.close()
        if ssh_sock:
            ssh_sock.close()
        return

    # 3. Stream data bidirectionally
    client_buffer = bytearray()
    sockets = [client_sock, ssh_sock]

    while True:
        try:
            r, _, e = select.select(sockets, [], sockets, 120)
            if e or not r:
                break

            for s in r:
                if s is client_sock:
                    data = client_sock.recv(BUFFER_SIZE)
                    if not data:
                        raise ConnectionResetError()
                    
                    if is_ws:
                        client_buffer.extend(data)
                        while True:
                            opcode, payload, remaining = parse_ws_frame(client_buffer)
                            if opcode is None:
                                break
                            
                            client_buffer = bytearray(remaining)
                            
                            # Handle WS Opcodes
                            if opcode == 0x8:  # Connection Close
                                raise ConnectionResetError()
                            elif opcode == 0x9:  # Ping -> Reply Pong
                                pong_frame = create_ws_frame(payload, opcode=0xA)
                                client_sock.sendall(pong_frame)
                            elif opcode in (0x1, 0x2):  # Text or Binary Frame
                                if payload:
                                    ssh_sock.sendall(payload)
                    else:
                        ssh_sock.sendall(data)

                elif s is ssh_sock:
                    data = ssh_sock.recv(BUFFER_SIZE)
                    if not data:
                        raise ConnectionResetError()
                    
                    if is_ws:
                        frame = create_ws_frame(data)
                        client_sock.sendall(frame)
                    else:
                        client_sock.sendall(data)
        except Exception:
            break

    try:
        client_sock.close()
        if ssh_sock:
            ssh_sock.close()
    except Exception:
        pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(1024)

    while True:
        try:
            client_sock, _ = server.accept()
            t = threading.Thread(target=handle_client, args=(client_sock,))
            t.daemon = True
            t.start()
        except Exception:
            continue

if __name__ == '__main__':
    main()
