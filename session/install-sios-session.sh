#!/bin/bash
# install-sios-session.sh — Installs the SIOS session layer on Ubuntu 24.04.
#
# This script:
#   1. Installs system dependencies (LightDM, Plymouth, Xorg, Godot).
#   2. Copies the SIOS runtime, desktop, and session files to /opt and /usr.
#   3. Registers the X session, display manager config, and systemd services.
#   4. Sets the Plymouth boot theme and GRUB branding.
#   5. Pulls the llama3.1:8b model if not already present.
#
# Run as root on the target Ubuntu 24.04 system.

set -euo pipefail

GOLD='\033[38;5;179m'
GREEN='\033[32m'
DIM='\033[2m'
OFF='\033[0m'

SIOS_SRC="$(cd "$(dirname "$0")/.." && pwd)"
SIOS_DST="/opt/sios-live"
DESKTOP_SRC="$SIOS_SRC/desktop"
DESKTOP_DST="/opt/sios-desktop"

echo -e "${GOLD}SIOS Session Installer${OFF}"
echo -e "${DIM}Source: $SIOS_SRC${OFF}"
echo -e "${DIM}Target: $SIOS_DST${OFF}"
echo ""

# ----------------------------------------------------------------- 1. deps
echo -e "${GOLD}[1/7]${OFF} Installing system dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    lightdm plymouth plymouth-label \
    xserver-xorg-core x11-xserver-utils \
    python3 python3-pip \
    curl wget unzip \
    fonts-cormorant-garamond fonts-inter \
    >/dev/null 2>&1
echo -e "  ${GREEN}OK${OFF}"

# ----------------------------------------------------------------- 2. godot
echo -e "${GOLD}[2/7]${OFF} Installing Godot 4..."
if command -v godot &>/dev/null && godot --version 2>/dev/null | grep -q "^4\."; then
    echo -e "  ${DIM}Godot 4 already installed${OFF}"
else
    cd /opt
    wget -q 'https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_linux.x86_64.zip' -O godot4.zip
    unzip -o godot4.zip >/dev/null 2>&1
    chmod +x Godot_v4.3-stable_linux.x86_64
    ln -sf /opt/Godot_v4.3-stable_linux.x86_64 /usr/local/bin/godot
    rm -f godot4.zip
    echo -e "  ${GREEN}Godot $(godot --version) installed${OFF}"
fi

# ----------------------------------------------------------------- 3. runtime
echo -e "${GOLD}[3/7]${OFF} Installing SIOS runtime..."
mkdir -p "$SIOS_DST"
cp -r "$SIOS_SRC/anubis" "$SIOS_DST/"
cp -r "$SIOS_SRC/tools" "$SIOS_DST/"
cp -r "$SIOS_SRC/tests" "$SIOS_DST/"
[ -d "$SIOS_SRC/skills" ] && cp -r "$SIOS_SRC/skills" "$SIOS_DST/" || true
[ -d "$SIOS_SRC/evidence" ] && cp -r "$SIOS_SRC/evidence" "$SIOS_DST/" || true
echo -e "  ${GREEN}Runtime installed to $SIOS_DST${OFF}"

# ----------------------------------------------------------------- 4. desktop
echo -e "${GOLD}[4/7]${OFF} Installing SIOS desktop..."
mkdir -p "$DESKTOP_DST"
cp -r "$DESKTOP_SRC"/* "$DESKTOP_DST/" 2>/dev/null || true
# Import the Godot project to generate .godot cache
cd "$DESKTOP_DST"
godot --headless --import 2>/dev/null || true
echo -e "  ${GREEN}Desktop installed to $DESKTOP_DST${OFF}"

# ----------------------------------------------------------------- 5. session
echo -e "${GOLD}[5/7]${OFF} Installing session and display manager..."
# X session entry
cp "$SIOS_SRC/session/sios.desktop" /usr/share/xsessions/sios.desktop
# Session launcher
cp "$SIOS_SRC/session/sios-session" /usr/local/bin/sios-session
chmod +x /usr/local/bin/sios-session
# LightDM config
mkdir -p /etc/lightdm/lightdm.conf.d
cp "$SIOS_SRC/session/lightdm-sios.conf" /etc/lightdm/lightdm.conf.d/10-sios.conf
# Brand assets
mkdir -p /usr/share/sios
cp "$DESKTOP_SRC/icon.svg" /usr/share/sios/icon.svg 2>/dev/null || true
# Set LightDM as default display manager
echo "/usr/sbin/lightdm" > /etc/X11/default-display-manager 2>/dev/null || true
echo -e "  ${GREEN}Session registered${OFF}"

# ----------------------------------------------------------------- 6. services
echo -e "${GOLD}[6/7]${OFF} Installing systemd services..."
cp "$SIOS_SRC/session/sios-anubis.service" /etc/systemd/system/sios-anubis.service
cp "$SIOS_SRC/session/ollama.service" /etc/systemd/system/ollama.service
systemctl daemon-reload
systemctl enable sios-anubis.service 2>/dev/null || true
systemctl enable ollama.service 2>/dev/null || true
echo -e "  ${GREEN}Services installed and enabled${OFF}"

# ----------------------------------------------------------------- 7. plymouth
echo -e "${GOLD}[7/7]${OFF} Installing boot theme..."
bash "$SIOS_SRC/session/install-plymouth-theme.sh" 2>/dev/null || true
plymouth-set-default-theme sios 2>/dev/null || true
# GRUB
cp "$SIOS_SRC/session/grub-sios.cfg" /etc/grub.d/40_sios 2>/dev/null || true
chmod +x /etc/grub.d/40_sios 2>/dev/null || true
update-grub 2>/dev/null || true
echo -e "  ${GREEN}Boot theme installed${OFF}"

# ----------------------------------------------------------------- model
echo ""
echo -e "${GOLD}Model setup:${OFF}"
if command -v ollama &>/dev/null; then
    if ! ollama list 2>/dev/null | grep -q "llama3.1:8b"; then
        echo -e "  ${DIM}Pulling llama3.1:8b (this will take a while)...${OFF}"
        ollama pull llama3.1:8b
    fi
    echo -e "  ${GREEN}llama3.1:8b available${OFF}"
else
    echo -e "  ${DIM}Ollama not installed — install it from https://ollama.com${OFF}"
fi

# ----------------------------------------------------------------- done
echo ""
echo -e "${GOLD}SIOS session installation complete.${OFF}"
echo ""
echo -e "Next steps:"
echo -e "  1. Reboot to enter the SIOS session"
echo -e "  2. LightDM will show the SIOS greeter"
echo -e "  3. Select 'SIOS' as the session and log in"
echo -e "  4. The spatial desktop will launch automatically"
echo ""
echo -e "${DIM}To test without rebooting:${OFF}"
echo -e "  ${DIM}startx /usr/local/bin/sios-session${OFF}"
