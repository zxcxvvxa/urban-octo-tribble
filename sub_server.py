import base64
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8000
SECRET_PATH = "/sub"

CONFIG = {
    "port": 443,
    "uuid": "cxlvin777",
    "password": "Cxlvin777",
    "ss_method": "chacha20-ietf-poly1305"
}

def extract_run_app_host(host_header):
    """Extracts host without port from HTTP Host header for authority/host."""
    if host_header:
        return host_header.split(':')[0]
    return "example.run.app"

def generate_subscription(host_header):
    run_app_host = extract_run_app_host(host_header)
    port = CONFIG["port"]
    uuid = CONFIG["uuid"]
    pwd = CONFIG["password"]
    ss_credentials = base64.b64encode(f"{CONFIG['ss_method']}:{pwd}".encode()).decode()

    links = []

    # 1. gRPC NODES
    # Address: firebase-settings.crashlytics.com | SNI: firebase-settings.crashlytics.com | ALPN: none | FP: none
    grpc_addr = "firebase-settings.crashlytics.com"
    grpc_sni = "firebase-settings.crashlytics.com"

    links.append(
        f"vless://{uuid}@{grpc_addr}:{port}?mode=gun&security=tls&encryption=none&insecure=0&type=grpc&serviceName=cxlvinvl-grpc&authority={run_app_host}&allowInsecure=0&sni={grpc_sni}#vless-grpc"
    )
    links.append(
        f"trojan://{pwd}@{grpc_addr}:{port}?mode=gun&security=tls&insecure=0&type=grpc&serviceName=cxlvintr-grpc&authority={run_app_host}&allowInsecure=0&sni={grpc_sni}#trojan-grpc"
    )
    vmess_grpc = {
        "v": "2", "ps": "vmess-grpc", "add": grpc_addr, "port": str(port), "id": uuid, "aid": "0", "scy": "auto",
        "net": "grpc", "type": "gun", "path": "cxlvinvm-grpc", "host": run_app_host, "tls": "tls", "sni": grpc_sni
    }
    links.append("vmess://" + base64.b64encode(json.dumps(vmess_grpc).encode()).decode())
    links.append(
        f"ss://{ss_credentials}@{grpc_addr}:{port}?mode=gun&security=tls&insecure=0&type=grpc&serviceName=cxlvinss-grpc&authority={run_app_host}&allowInsecure=0&sni={grpc_sni}#ss-grpc"
    )

    # 2. WEBSOCKET NODES
    # Address: app-analytics-services.com | SNI: app-analytics-services.com | ALPN: none | FP: none
    ws_addr = "app-analytics-services.com"
    ws_sni = "app-analytics-services.com"

    links.append(
        f"vless://{uuid}@{ws_addr}:{port}?encryption=none&type=ws&headerType=none&path=%2FCxlvinVlWS%3Fed%3D2560&security=tls&host={run_app_host}&sni={ws_sni}#vless-ws"
    )
    links.append(
        f"trojan://{pwd}@{ws_addr}:{port}?type=ws&headerType=none&path=%2FCxlvinTRWS%3Fed%3D2560&security=tls&host={run_app_host}&sni={ws_sni}#trojan-ws"
    )
    vmess_ws = {
        "v": "2", "ps": "vmess-ws", "add": ws_addr, "port": str(port), "id": uuid, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "path": "/CxlvinVMWS?ed=2560", "host": run_app_host, "tls": "tls", "sni": ws_sni
    }
    links.append("vmess://" + base64.b64encode(json.dumps(vmess_ws).encode()).decode())
    links.append(
        f"ss://{ss_credentials}@{ws_addr}:{port}?type=ws&headerType=none&path=%2FCxlvinSSWS%3Fed%3D2560&security=tls&host={run_app_host}&sni={ws_sni}#ss-ws"
    )

    # 3. HTTP UPGRADE NODES
    # Address: fcmtoken.googleapis.com | SNI: fcmtoken.googleapis.com | ALPN: http/1.1 | FP: none
    hu_addr = "fcmtoken.googleapis.com"
    hu_sni = "fcmtoken.googleapis.com"

    links.append(
        f"vless://{uuid}@{hu_addr}:{port}?encryption=none&type=httpupgrade&headerType=none&path=%2FCxlvinVlHU%3Fed%3D2560&security=tls&alpn=http%2F1.1&host={run_app_host}&sni={hu_sni}#vless-hu"
    )
    links.append(
        f"trojan://{pwd}@{hu_addr}:{port}?type=httpupgrade&headerType=none&path=%2FCxlvinTRHU%3Fed%3D2560&security=tls&alpn=http%2F1.1&host={run_app_host}&sni={hu_sni}#trojan-hu"
    )
    vmess_hu = {
        "v": "2", "ps": "vmess-hu", "add": hu_addr, "port": str(port), "id": uuid, "aid": "0", "scy": "auto",
        "net": "httpupgrade", "type": "none", "path": "/CxlvinVMHU?ed=2560", "host": run_app_host, "tls": "tls", "sni": hu_sni, "alpn": "http/1.1"
    }
    links.append("vmess://" + base64.b64encode(json.dumps(vmess_hu).encode()).decode())
    links.append(
        f"ss://{ss_credentials}@{hu_addr}:{port}?type=httpupgrade&headerType=none&path=%2FCxlvinSSHU%3Fed%3D2560&security=tls&alpn=http%2F1.1&host={run_app_host}&sni={hu_sni}#ss-hu"
    )

    # 4. XHTTP NODES
    # Address: firebaseremoteconfigrealtime.googleapis.com | SNI: firebaseremoteconfigrealtime.googleapis.com | ALPN: h2 | FP: none
    xh_addr = "firebaseremoteconfigrealtime.googleapis.com"
    xh_sni = "firebaseremoteconfigrealtime.googleapis.com"

    links.append(
        f"vless://{uuid}@{xh_addr}:{port}?encryption=none&type=xhttp&headerType=stream-one&path=%2FCxlvinVlXH%3Fed%3D2560&security=tls&alpn=h2&host={run_app_host}&sni={xh_sni}#vless-xhttp"
    )
    links.append(
        f"trojan://{pwd}@{xh_addr}:{port}?type=xhttp&headerType=stream-one&path=%2FCxlvinTRXH%3Fed%3D2560&security=tls&alpn=h2&host={run_app_host}&sni={xh_sni}#trojan-xhttp"
    )
    vmess_xh = {
        "v": "2", "ps": "vmess-xhttp", "add": xh_addr, "port": str(port), "id": uuid, "aid": "0", "scy": "auto",
        "net": "xhttp", "type": "stream-one", "path": "/CxlvinVMXH?ed=2560", "host": run_app_host, "tls": "tls", "sni": xh_sni, "alpn": "h2"
    }
    links.append("vmess://" + base64.b64encode(json.dumps(vmess_xh).encode()).decode())
    links.append(
        f"ss://{ss_credentials}@{xh_addr}:{port}?type=xhttp&headerType=stream-one&path=%2FCxlvinSSXH%3Fed%3D2560&security=tls&alpn=h2&host={run_app_host}&sni={xh_sni}#ss-xhttp"
    )

    raw_payload = "\n".join(links)
    return base64.b64encode(raw_payload.encode('utf-8'))

class SubHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        host_header = self.headers.get('Host', '')
        
        if self.path == SECRET_PATH or self.path.startswith(f"{SECRET_PATH}?"):
            sub_body = generate_subscription(host_header)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Profile-Update-Interval', '24')
            self.end_headers()
            self.wfile.write(sub_body)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), SubHandler)
    print(f"Subscription server running on port {PORT}...")
    server.serve_forever()
