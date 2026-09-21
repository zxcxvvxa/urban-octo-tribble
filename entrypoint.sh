#!/bin/bash
set -e

echo "[+] Starting container initialization..."

# 1. File Descriptor Limits
# Increases file descriptors for high concurrency (fallbacks safely if restricted)
ulimit -n 65535 2>/dev/null || true

# 2. Kernel & TCP Socket Tuning
# Requires runtime capabilities (--cap-add=NET_ADMIN / --privileged)
# Suppresses errors gracefully in restricted container environments (e.g. GCP Cloud Run)
echo "[+] Attempting Kernel & TCP Socket Tuning..."

sysctl -w net.core.default_qdisc=fq 2>/dev/null || true
sysctl -w net.ipv4.tcp_congestion_control=bbr 2>/dev/null || true

# Maximize socket memory buffers (16MB max)
sysctl -w net.core.rmem_max=16777216 2>/dev/null || true
sysctl -w net.core.wmem_max=16777216 2>/dev/null || true
sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216" 2>/dev/null || true
sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216" 2>/dev/null || true

# Fast socket recycling, low FIN timeouts, and TCP Fast Open
sysctl -w net.ipv4.tcp_fin_timeout=15 2>/dev/null || true
sysctl -w net.ipv4.tcp_tw_reuse=1 2>/dev/null || true
sysctl -w net.ipv4.tcp_fastopen=3 2>/dev/null || true

# 3. SSH Setup & App Permissions
echo "[+] Generating SSH Host Keys and setting up runtime directories..."
ssh-keygen -A 2>/dev/null || true
mkdir -p /run/sshd /var/run/sshd
chmod +x /app/*.py 2>/dev/null || true

# 4. Process Handover
if [ "$#" -gt 0 ]; then
    echo "[+] Handing over execution to CMD: $@"
    exec "$@"
else
    echo "[+] Handing over process management to Supervisor..."
    exec /usr/bin/supervisord -c /etc/supervisord.conf
fi
