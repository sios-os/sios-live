#!/usr/bin/env bash
# setup_vpn.sh — Configure IONOS VPS Linux S+ as a VPN endpoint for SIOS.
#
# This script runs ON the VPS (not locally). It:
#   1. Updates the system
#   2. Installs WireGuard
#   3. Generates server and client keys
#   4. Configures the WireGuard server
#   5. Sets up firewall rules
#   6. Enables IP forwarding
#   7. Starts the VPN
#
# Usage:
#   ssh root@<VPS_IP> 'bash -s' < tools/setup_vpn.sh
#
# Or copy and run directly on the VPS:
#   scp tools/setup_vpn.sh root@<VPS_IP>:/root/
#   ssh root@<VPS_IP> 'bash /root/setup_vpn.sh'
#
# After setup, the client config will be printed. Save it to
# /etc/wireguard/wg0.conf on the SIOS machine.
#
# Security notes:
#   - Change the default SSH password after first login
#   - The WireGuard port defaults to 51820
#   - The VPN subnet is 10.66.66.0/24
#   - All traffic is encrypted end-to-end
#   - No logs are kept on the VPS beyond standard system logs

set -euo pipefail

# Configuration
WG_PORT=51820
VPN_SUBNET="10.66.66.0/24"
SERVER_IP="10.66.66.1"
CLIENT_IP="10.66.66.2"
WG_INTERFACE="wg0"

echo "=== SIOS VPN Setup (IONOS VPS Linux S+) ==="
echo ""

# Step 1: System update
echo "[1/7] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Step 2: Install WireGuard
echo "[2/7] Installing WireGuard..."
apt-get install -y -qq wireguard wireguard-tools qrencode

# Step 3: Generate keys
echo "[3/7] Generating WireGuard keys..."
mkdir -p /etc/wireguard
cd /etc/wireguard

# Server keys
if [ ! -f server_private.key ]; then
    wg genkey > server_private.key
    wg pubkey < server_private.key > server_public.key
    chmod 600 server_private.key
    echo "  Server keys generated."
else
    echo "  Server keys already exist, reusing."
fi

# Client keys (for the SIOS machine)
if [ ! -f client_private.key ]; then
    wg genkey > client_private.key
    wg pubkey < client_private.key > client_public.key
    chmod 600 client_private.key
    echo "  Client keys generated."
else
    echo "  Client keys already exist, reusing."
fi

SERVER_PRIVATE=$(cat server_private.key)
SERVER_PUBLIC=$(cat server_public.key)
CLIENT_PRIVATE=$(cat client_private.key)
CLIENT_PUBLIC=$(cat client_public.key)

# Step 4: Configure WireGuard server
echo "[4/7] Configuring WireGuard server..."
cat > /etc/wireguard/${WG_INTERFACE}.conf << EOF
[Interface]
Address = ${SERVER_IP}/24
PrivateKey = ${SERVER_PRIVATE}
ListenPort = ${WG_PORT}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = ${CLIENT_PUBLIC}
AllowedIPs = ${CLIENT_IP}/32
EOF
chmod 600 /etc/wireguard/${WG_INTERFACE}.conf

# Step 5: Firewall rules
echo "[5/7] Configuring firewall..."
# Allow SSH (don't lock ourselves out)
iptables -C INPUT -p tcp --dport 22 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# Allow WireGuard
iptables -C INPUT -p udp --dport ${WG_PORT} -j ACCEPT 2>/dev/null || iptables -A INPUT -p udp --dport ${WG_PORT} -j ACCEPT
# Allow established connections
iptables -C INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
# Allow loopback
iptables -C INPUT -i lo -j ACCEPT 2>/dev/null || iptables -A INPUT -i lo -j ACCEPT

# Step 6: Enable IP forwarding
echo "[6/7] Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi

# Step 7: Start WireGuard
echo "[7/7] Starting WireGuard..."
systemctl enable wg-quick@${WG_INTERFACE}
wg-quick down ${WG_INTERFACE} 2>/dev/null || true
wg-quick up ${WG_INTERFACE}

echo ""
echo "=== VPN Setup Complete ==="
echo ""
echo "Server public key: $(cat server_public.key)"
echo "VPN server IP: ${SERVER_IP}"
echo "VPN client IP: ${CLIENT_IP}"
echo "WireGuard port: ${WG_PORT}"
echo ""
echo "=== CLIENT CONFIGURATION (save to /etc/wireguard/wg0.conf on SIOS) ==="
echo ""
cat << CLIENT_CONF
[Interface]
PrivateKey = ${CLIENT_PRIVATE}
Address = ${CLIENT_IP}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = ${SERVER_PUBLIC}
Endpoint = $(curl -s ifconfig.me):${WG_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
CLIENT_CONF
echo ""
echo "=== QR Code (optional, for mobile clients) ==="
qrencode -t ANSIUTF8 << QR_EOF 2>/dev/null || echo "(QR code skipped - use 'qrencode -t ansiutf8 < config/wg0-client.conf' locally)"
[Interface]
PrivateKey = ${CLIENT_PRIVATE}
Address = ${CLIENT_IP}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = ${SERVER_PUBLIC}
Endpoint = $(curl -s ifconfig.me):${WG_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
QR_EOF
echo ""
echo "=== Security Recommendations ==="
echo "1. Change the root password: passwd"
echo "2. Disable password SSH auth (use keys only):"
echo "   Edit /etc/ssh/sshd_config, set PasswordAuthentication no"
echo "3. Install fail2ban: apt-get install fail2ban"
echo "4. Review WireGuard status: wg show"
echo ""
echo "Done. The VPN is now running."
