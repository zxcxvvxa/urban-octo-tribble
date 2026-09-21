FROM alpine:3.20 AS xray-bin

RUN apk add --no-cache \
    curl \
    unzip \
    ca-certificates \
    bash

WORKDIR /app

RUN curl -L --retry 3 "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip" -o xray.zip \
    || curl -L --retry 3 "https://ghproxy.com/https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip" -o xray.zip \
    && unzip xray.zip \
    && chmod +x xray \
    && mv xray /usr/local/bin/xray \
    && rm -f xray.zip

FROM openresty/openresty:alpine-fat

ENV TZ=Asia/Shanghai

RUN apk add --no-cache \
    ca-certificates \
    bash \
    curl \
    tzdata \
    wget \
    supervisor \
    python3 \
    py3-pip \
    iptables \
    openssh-server \
    openssh-sftp-server

# Install Lua WebSocket module for OpenResty
RUN /usr/local/openresty/bin/opm get openresty/lua-resty-websocket

# Download static badvpn-udpgw binary
RUN curl -L -o /usr/local/bin/badvpn-udpgw https://raw.githubusercontent.com/daybreaker/badvpn-udpgw-binaries/master/badvpn-udpgw-x86_64 \
    || wget -O /usr/local/bin/badvpn-udpgw https://github.com/ambrop72/badvpn/releases/download/1.999.130/badvpn-1.999.130.tar.bz2 \
    && chmod +x /usr/local/bin/badvpn-udpgw

WORKDIR /app

# Copy banner file
COPY banner.txt /etc/banner.txt

# Configure OpenSSH & Create User Safely
RUN mkdir -p /var/run/sshd \
    && ssh-keygen -A \
    && adduser -D -s /bin/bash cxlvin \
    && echo 'cxlvin:cxlvin' | chpasswd \
    && echo 'root:cxlvin' | chpasswd

# Configure OpenSSH for local listening without protocol-breaking features
RUN { \
    echo "Port 22"; \
    echo "ListenAddress 127.0.0.1"; \
    echo "PermitRootLogin yes"; \
    echo "PubkeyAuthentication yes"; \
    echo "PasswordAuthentication yes"; \
    echo "AllowTcpForwarding yes"; \
    echo "AllowAgentForwarding yes"; \
    echo "GatewayPorts yes"; \
    echo "PermitTunnel yes"; \
    echo "PermitOpen any"; \
    echo "X11Forwarding yes"; \
    echo "UseDNS no"; \
    echo "TCPKeepAlive yes"; \
    echo "ClientAliveInterval 15"; \
    echo "ClientAliveCountMax 3"; \
    echo "MaxSessions 100"; \
    echo "MaxStartups 100:30:200"; \
    echo "Compression no"; \
    echo "Subsystem sftp /usr/libexec/sftp-server"; \
    } > /etc/ssh/sshd_config

# Copy Xray binary
COPY --from=xray-bin /usr/local/bin/xray /usr/local/bin/xray
RUN chmod +x /usr/local/bin/xray

# Copy Python scripts & configs
COPY sub_server.py /app/sub_server.py
COPY anti_ddos.py /app/anti_ddos.py
COPY log_cleaner.py /app/log_cleaner.py
COPY entrypoint.sh /app/entrypoint.sh

COPY config.json /etc/xray.json
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY supervisord.conf /etc/supervisord.conf

RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
CMD wget -qO- http://127.0.0.1:8080/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
