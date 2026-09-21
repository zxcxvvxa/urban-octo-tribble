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
    openssh-sftp-server \
    badvpn

WORKDIR /app

# Copy banner file
COPY banner.txt /etc/banner.txt

# Configure SSH
RUN mkdir -p /var/run/sshd \
    && ssh-keygen -A \
    && adduser -D -s /bin/bash cxlvin \
    && echo 'cxlvin:cxlvin' | chpasswd

RUN { \
    echo "PermitRootLogin yes"; \
    echo "PasswordAuthentication yes"; \
    echo "AllowTcpForwarding yes"; \
    echo "AllowAgentForwarding yes"; \
    echo "GatewayPorts yes"; \
    echo "PermitTunnel yes"; \
    echo "UseDNS no"; \
    echo "TCPKeepAlive yes"; \
    echo "ClientAliveInterval 15"; \
    echo "ClientAliveCountMax 3"; \
    echo "MaxSessions 50"; \
    echo "MaxStartups 50:30:100"; \
    echo "Compression no"; \
    echo "Banner /etc/banner.txt"; \
    } >> /etc/ssh/sshd_config

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
CMD wget -qO- http://[::1]:8080/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
