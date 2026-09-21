#!/bin/bash
set -e

echo "[+] Starting container initialization..."

# 1. File Descriptor Limits
# Increases file descriptors for high concurrency (fallback safely if restricted)
ulimit -n 65535 2>/dev/null || true

# 2. Kernel & TCP Socket Tuning
# Requires runtime capabilities (--cap-add=SYS_ADMIN or --privileged) to apply.
# Suppresses errors gracefully in restricted container environments like Cloud Run where /proc/sys is read-only.
echo "[+] Attempting Kernel & TCP Socket Tuning..."

# Enable BBR Congestion Control
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

# 3. SSH Setup
echo "[+] Generating SSH Host Keys and setup runtime directories..."
ssh-keygen -A 2>/dev/null || true
mkdir -p /run/sshd /var/run/sshd

# 4. Process Handover
# Pass control directly to Docker/Container CMD or default process manager
if [ "$#" -gt 0 ]; then
    echo "[+] Handing over execution to CMD: $@"
    exec "$@"
else
    echo "[+] Handing over process management to Supervisor..."
    exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
fi
