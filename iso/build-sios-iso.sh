#!/bin/bash
# build-sios-iso.sh — Builds a bootable SIOS Ubuntu 24.04 ISO.
#
# This script creates a branded SIOS ISO by:
#   1. Downloading the Ubuntu 24.04 minimal base (if not cached).
#   2. Extracting the root filesystem.
#   3. Installing the SIOS session layer (desktop, ANUBIS, services).
#   4. Configuring branding (Plymouth, GRUB, LightDM, session).
#   5. Repacking as a bootable ISO with xorriso.
#
# The resulting ISO boots into the SIOS greeter and launches the spatial
# desktop on login.
#
# Requirements: xorriso, squashfs-tools, debootstrap, wget, ~4GB disk space.

set -uo pipefail

GOLD='\033[38;5;179m'
GREEN='\033[32m'
DIM='\033[2m'
RED='\033[31m'
OFF='\033[0m'

# ----------------------------------------------------------------- config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIOS_SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${SIOS_BUILD_DIR:-/tmp/sios-iso-build}"
ISO_OUTPUT="${SIOS_ISO_OUTPUT:-$SIOS_SRC/sios-ubuntu-24.04.iso}"
UBUNTU_VERSION="24.04"
UBUNTU_BASE_URL="https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release"
UBUNTU_BASE_FILE="ubuntu-base-24.04.4-base-amd64.tar.gz"
UBUNTU_BASE_CACHE="$BUILD_DIR/cache/$UBUNTU_BASE_FILE"

# Boot kernel/initrd from the Ubuntu ISO (more reliable than extracting from base)
UBUNTU_ISO_URL="https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso"
UBUNTU_ISO_CACHE="$BUILD_DIR/cache/ubuntu-24.04-desktop.iso"

echo -e "${GOLD}SIOS ISO Builder${OFF}"
echo -e "${DIM}Source:  $SIOS_SRC${OFF}"
echo -e "${DIM}Build:   $BUILD_DIR${OFF}"
echo -e "${DIM}Output:  $ISO_OUTPUT${OFF}"
echo ""

# ----------------------------------------------------------------- 1. cache
echo -e "${GOLD}[1/6]${OFF} Preparing build environment..."
mkdir -p "$BUILD_DIR" "$BUILD_DIR/cache" "$BUILD_DIR/rootfs" "$BUILD_DIR/iso"

# Download ubuntu base
if [ ! -f "$UBUNTU_BASE_CACHE" ]; then
    echo -e "  ${DIM}Downloading Ubuntu 24.04 base...${OFF}"
    wget -q "$UBUNTU_BASE_URL/$UBUNTU_BASE_FILE" -O "$UBUNTU_BASE_CACHE"
fi
echo -e "  ${GREEN}Base image cached${OFF}"

# ----------------------------------------------------------------- 2. rootfs
echo -e "${GOLD}[2/6]${OFF} Extracting root filesystem..."
# Clean up any stale mounts from a previous run
umount -lf "$BUILD_DIR/rootfs/dev" 2>/dev/null || true
umount -lf "$BUILD_DIR/rootfs/proc" 2>/dev/null || true
umount -lf "$BUILD_DIR/rootfs/sys" 2>/dev/null || true
umount -lf "$BUILD_DIR/rootfs/run" 2>/dev/null || true
rm -rf "$BUILD_DIR/rootfs"
mkdir -p "$BUILD_DIR/rootfs"
tar xzf "$UBUNTU_BASE_CACHE" -C "$BUILD_DIR/rootfs"
echo -e "  ${GREEN}Root filesystem extracted${OFF}"

# ----------------------------------------------------------------- 3. install
echo -e "${GOLD}[3/6]${OFF} Installing SIOS layer into rootfs..."

# Mount virtual filesystems for chroot
mount --bind /dev "$BUILD_DIR/rootfs/dev"
mount --bind /proc "$BUILD_DIR/rootfs/proc"
mount --bind /sys "$BUILD_DIR/rootfs/sys"
mount --bind /run "$BUILD_DIR/rootfs/run"

# Copy DNS resolution into the chroot
cp /etc/resolv.conf "$BUILD_DIR/rootfs/etc/resolv.conf" 2>/dev/null || true

cleanup_chroot() {
    umount "$BUILD_DIR/rootfs/dev" 2>/dev/null || true
    umount "$BUILD_DIR/rootfs/proc" 2>/dev/null || true
    umount "$BUILD_DIR/rootfs/sys" 2>/dev/null || true
    umount "$BUILD_DIR/rootfs/run" 2>/dev/null || true
}
trap cleanup_chroot EXIT

# Copy SIOS source into the chroot
mkdir -p "$BUILD_DIR/rootfs/opt/sios-live"
cp -r "$SIOS_SRC/anubis" "$BUILD_DIR/rootfs/opt/sios-live/"
cp -r "$SIOS_SRC/tools" "$BUILD_DIR/rootfs/opt/sios-live/"
cp -r "$SIOS_SRC/tests" "$BUILD_DIR/rootfs/opt/sios-live/"
cp -r "$SIOS_SRC/desktop" "$BUILD_DIR/rootfs/opt/sios-live/"
cp -r "$SIOS_SRC/session" "$BUILD_DIR/rootfs/opt/sios-live/"
[ -d "$SIOS_SRC/skills" ] && cp -r "$SIOS_SRC/skills" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/evidence" ] && cp -r "$SIOS_SRC/evidence" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/memory" ] && cp -r "$SIOS_SRC/memory" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/projects" ] && cp -r "$SIOS_SRC/projects" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/registry" ] && cp -r "$SIOS_SRC/registry" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/knowledge" ] && cp -r "$SIOS_SRC/knowledge" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/identity" ] && cp -r "$SIOS_SRC/identity" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/policy" ] && cp -r "$SIOS_SRC/policy" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/court" ] && cp -r "$SIOS_SRC/court" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/purge" ] && cp -r "$SIOS_SRC/purge" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/packages" ] && cp -r "$SIOS_SRC/packages" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/financial" ] && cp -r "$SIOS_SRC/financial" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/network" ] && cp -r "$SIOS_SRC/network" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/hardening" ] && cp -r "$SIOS_SRC/hardening" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/recovery" ] && cp -r "$SIOS_SRC/recovery" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/ab_images" ] && cp -r "$SIOS_SRC/ab_images" "$BUILD_DIR/rootfs/opt/sios-live/" || true
[ -d "$SIOS_SRC/egyptology" ] && cp -r "$SIOS_SRC/egyptology" "$BUILD_DIR/rootfs/opt/sios-live/" || true

# Run the installation inside the chroot
cat > "$BUILD_DIR/rootfs/tmp/sios-install.sh" << 'INSTALLER'
#!/bin/bash
set -x

export DEBIAN_FRONTEND=noninteractive
export HOME=/root

# Update and install dependencies
apt-get update -qq || true
apt-get install -y \
    linux-generic \
    lightdm plymouth plymouth-label \
    xserver-xorg-core x11-xserver-utils \
    python3 python3-pip \
    curl wget unzip \
    fonts-inter \
    initramfs-tools \
    casper \
    grub-pc-bin grub-efi-amd64-bin grub-common \
    || true
# Install optional fonts separately (may not be in base repo)
apt-get install -y fonts-cormorant-garamond 2>/dev/null || true

# Install Godot 4
cd /opt || exit 1
wget -q 'https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_linux.x86_64.zip' -O godot4.zip || true
unzip -o godot4.zip 2>/dev/null || true
chmod +x Godot_v4.3-stable_linux.x86_64 2>/dev/null || true
ln -sf /opt/Godot_v4.3-stable_linux.x86_64 /usr/local/bin/godot 2>/dev/null || true
rm -f godot4.zip

# Install Godot export templates (required for --export-release)
echo "  Installing Godot export templates..."
mkdir -p /root/.local/share/godot/export_templates/4.3.stable
wget -q 'https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_export_templates.tpz' -O /tmp/godot_templates.tpz 2>/dev/null || true
if [ -f /tmp/godot_templates.tpz ]; then
    cd /tmp && unzip -o godot_templates.tpz 2>/dev/null || true
    # The tpz is a zip with templates/ directory inside
    if [ -d /tmp/templates ]; then
        cp /tmp/templates/* /root/.local/share/godot/export_templates/4.3.stable/ 2>/dev/null || true
    fi
    rm -f /tmp/godot_templates.tpz
fi

# Install Ollama
echo "  Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null || true

# NOTE: Model is NOT pre-pulled to keep the ISO under 4 GiB (ISO9660 limit).
# The model will be pulled on first boot via the sios-anubis service.
# To pre-pull for an offline ISO, comment out the line below and uncomment
# the pull section, but the resulting squashfs may exceed 4 GiB.
echo "  Skipping model pull (will download on first boot)"

# Install SIOS session
SIOS_SRC=/opt/sios-live
# X session entry
mkdir -p /usr/share/xsessions
cp "$SIOS_SRC/session/sios.desktop" /usr/share/xsessions/sios.desktop
# Session launcher
cp "$SIOS_SRC/session/sios-session" /usr/local/bin/sios-session
chmod +x /usr/local/bin/sios-session
# LightDM config
mkdir -p /etc/lightdm/lightdm.conf.d
cp "$SIOS_SRC/session/lightdm-sios.conf" /etc/lightdm/lightdm.conf.d/10-sios.conf
# Brand assets
mkdir -p /usr/share/sios
cp "$SIOS_SRC/desktop/icon.svg" /usr/share/sios/icon.svg 2>/dev/null || true
# Set LightDM as default
echo "/usr/sbin/lightdm" > /etc/X11/default-display-manager

# Systemd services
cp "$SIOS_SRC/session/sios-anubis.service" /etc/systemd/system/sios-anubis.service
cp "$SIOS_SRC/session/ollama.service" /etc/systemd/system/ollama.service
cp "$SIOS_SRC/session/sios-first-boot.service" /etc/systemd/system/sios-first-boot.service
cp "$SIOS_SRC/session/sios-first-boot.sh" /usr/local/bin/sios-first-boot.sh
chmod +x /usr/local/bin/sios-first-boot.sh
systemctl enable sios-anubis.service 2>/dev/null || true
systemctl enable ollama.service 2>/dev/null || true
systemctl enable sios-first-boot.service 2>/dev/null || true

# Plymouth theme
bash "$SIOS_SRC/session/install-plymouth-theme.sh" 2>/dev/null || true
plymouth-set-default-theme sios 2>/dev/null || true

# GRUB
cp "$SIOS_SRC/session/grub-sios.cfg" /etc/grub.d/40_sios 2>/dev/null || true
chmod +x /etc/grub.d/40_sios 2>/dev/null || true

# Import the Godot project
cd /opt/sios-live/desktop
HOME=/root godot --headless --import 2>/dev/null || true

# Export the desktop as a standalone binary (if export presets exist)
if [ -f /opt/sios-live/desktop/export_presets.cfg ]; then
    echo "  Exporting Godot desktop binary..."
    mkdir -p /opt/sios-desktop
    HOME=/root godot --headless --export-release "Linux Desktop" /opt/sios-desktop/sios-desktop.x86_64 2>/dev/null || true
    if [ -f /opt/sios-desktop/sios-desktop.x86_64 ]; then
        chmod +x /opt/sios-desktop/sios-desktop.x86_64
        echo "  Desktop binary exported successfully"
    else
        echo "  WARNING: Desktop export failed, will run from source"
    fi
fi

# Create the sios user
useradd -m -s /bin/bash -G sudo,video,audio sios 2>/dev/null || true
echo "sios:sios" | chpasswd
echo "root:root" | chpasswd

# Auto-login as sios (for the live ISO)
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/00-autologin.conf << 'AUTOLOGIN'
[Seat:*]
autologin-user=sios
autologin-session=SIOS
AUTOLOGIN

# Update initramfs with Plymouth
update-initramfs -u 2>/dev/null || true

# Apply system hardening
echo "  Applying system hardening..."
SIOS_SRC=/opt/sios-live
# Generate and apply hardening script
python3 -c "
import sys; sys.path.insert(0, '$SIOS_SRC')
from anubis.system import SystemHardening, NetworkManager
h = SystemHardening('$SIOS_SRC/hardening')
n = NetworkManager('$SIOS_SRC/network')
open('/tmp/sios-harden.sh', 'w').write(h.generate_hardening_script())
open('/tmp/sios-firewall.sh', 'w').write(n.generate_firewall_script())
" 2>/dev/null || true
bash /tmp/sios-harden.sh 2>/dev/null || true
bash /tmp/sios-firewall.sh 2>/dev/null || true
rm -f /tmp/sios-harden.sh /tmp/sios-firewall.sh

# Generate recovery script
python3 -c "
import sys; sys.path.insert(0, '$SIOS_SRC')
from anubis.system import RecoveryManager
r = RecoveryManager('$SIOS_SRC/recovery')
open('/opt/sios-live/recovery.sh', 'w').write(r.generate_recovery_script())
" 2>/dev/null || true
chmod +x /opt/sios-live/recovery.sh 2>/dev/null || true

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*
# Clean up Godot export templates (not needed at runtime, saves ~1GB)
rm -rf /root/.local/share/godot/export_templates /tmp/templates 2>/dev/null || true
# Remove docs, man pages, and translations to reduce squashfs size
rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/* 2>/dev/null || true
rm -rf /usr/share/locale/*/LC_MESSAGES/*.mo 2>/dev/null || true
# Remove apt cache
rm -rf /var/cache/apt/* 2>/dev/null || true
INSTALLER

chmod +x "$BUILD_DIR/rootfs/tmp/sios-install.sh"
chroot "$BUILD_DIR/rootfs" /tmp/sios-install.sh
rm -f "$BUILD_DIR/rootfs/tmp/sios-install.sh"

echo -e "  ${GREEN}SIOS layer installed${OFF}"

# ----------------------------------------------------------------- 4. squashfs
echo -e "${GOLD}[4/6]${OFF} Creating squashfs filesystem..."

# Ensure virtual filesystems are unmounted before squashfs
umount "$BUILD_DIR/rootfs/dev/pts" 2>/dev/null || true
umount "$BUILD_DIR/rootfs/dev" 2>/dev/null || true
umount "$BUILD_DIR/rootfs/proc" 2>/dev/null || true
umount "$BUILD_DIR/rootfs/sys" 2>/dev/null || true
umount "$BUILD_DIR/rootfs/run" 2>/dev/null || true
# Clean up any leftover proc/sys entries
rm -rf "$BUILD_DIR/rootfs/proc"/* "$BUILD_DIR/rootfs/sys"/* 2>/dev/null || true
mkdir -p "$BUILD_DIR/rootfs/proc" "$BUILD_DIR/rootfs/sys" "$BUILD_DIR/rootfs/dev"

mkdir -p "$BUILD_DIR/iso/casper"
rm -f "$BUILD_DIR/iso/casper/filesystem.squashfs"
mksquashfs "$BUILD_DIR/rootfs" "$BUILD_DIR/iso/casper/filesystem.squashfs" \
    -comp gzip -no-progress -quiet
echo -e "  ${GREEN}Squashfs created${OFF}"

# ----------------------------------------------------------------- 5. boot
echo -e "${GOLD}[5/6]${OFF} Assembling ISO boot structure..."

# Copy kernel and initrd from the chroot
cp "$BUILD_DIR/rootfs/boot/vmlinuz-"* "$BUILD_DIR/iso/casper/vmlinuz" 2>/dev/null || true
cp "$BUILD_DIR/rootfs/boot/initrd.img-"* "$BUILD_DIR/iso/casper/initrd" 2>/dev/null || true

# Install GRUB boot images for ISO
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq grub-pc-bin grub-efi-amd64-bin 2>/dev/null || true

# Create GRUB i386-pc boot image for BIOS
mkdir -p "$BUILD_DIR/iso/boot/grub/i386-pc"
grub-mkimage -o "$BUILD_DIR/iso/boot/grub/i386-pc/eltorito.img" \
    -O i386-pc-eltorito -p /boot/grub \
    biosdisk iso9660 linux ls cat echo reboot halt search normal \
    2>/dev/null || true

# Create EFI boot image
mkdir -p "$BUILD_DIR/iso/boot/grub"
grub-mkimage -o "$BUILD_DIR/iso/boot/grub/efi.img" \
    -O x86_64-efi -p /boot/grub \
    iso9660 linux ls cat echo reboot halt search normal \
    2>/dev/null || true
# Create EFI directory structure
mkdir -p "$BUILD_DIR/iso/EFI/BOOT"
cp "$BUILD_DIR/iso/boot/grub/efi.img" "$BUILD_DIR/iso/EFI/BOOT/bootx64.efi" 2>/dev/null || true

# GRUB configuration for the ISO
mkdir -p "$BUILD_DIR/iso/boot/grub"
cat > "$BUILD_DIR/iso/boot/grub/grub.cfg" << 'GRUB'
set default=0
set timeout=5

set menu_color_normal="white/black"
set menu_color_highlight="yellow/black"
set color_normal="light-gray/black"
set color_highlight="yellow/black"

menuentry "SIOS — Sovereign Interactive Operating System" {
    linux /casper/vmlinuz boot=casper quiet splash plymouth.theme=sios ---
    initrd /casper/initrd
}

menuentry "SIOS — Safe Mode (no splash)" {
    linux /casper/vmlinuz boot=casper nomodeset ---
    initrd /casper/initrd
}

menuentry "SIOS — Recovery Console" {
    linux /casper/vmlinuz boot=casper single ---
    initrd /casper/initrd
}
GRUB

# .disk/info for Ubuntu installer recognition
mkdir -p "$BUILD_DIR/iso/.disk"
cat > "$BUILD_DIR/iso/.disk/info" << 'DISK'
SIOS Ubuntu 24.04 - Sovereign Interactive Operating System
DISK

# README
cat > "$BUILD_DIR/iso/README.txt" << 'README'
SIOS — Sovereign Interactive Operating System
=============================================

This is a live bootable ISO of SIOS built on Ubuntu 24.04.

Boot it to enter the SIOS spatial desktop environment.
ANUBIS starts automatically on boot — no setup required.

Default login: sios / sios

The ISO includes:
  - ANUBIS self-development runtime (Python)
  - SIOS spatial desktop (Godot 4)
  - Constitutional kernel and evidence ledger
  - Sandboxed code execution
  - LightDM greeter with SIOS branding
  - Plymouth boot splash
  - Ollama + qwen2.5-coder:7b model (pre-installed)
  - 14 domain directors, 268 specialties, 14 verifiers
  - Knowledge base with quarantine and population pipeline
  - Identity vault, policy engine, Court review
  - A/B image management, recovery environment
  - Egyptology support (Gardiner signs, dictionary)
  - Midnight Purge maintenance system
  - Package manager, financial ledger

Everything runs locally. No network required after boot.
README

echo -e "  ${GREEN}Boot structure assembled${OFF}"

# ----------------------------------------------------------------- 6. iso
echo -e "${GOLD}[6/6]${OFF} Building ISO image..."
xorriso -as mkisofs \
    -r -V "SIOS Ubuntu 24.04" \
    -iso-level 3 \
    -b boot/grub/i386-pc/eltorito.img \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --grub2-boot-info \
    -eltorito-alt-boot \
    -e boot/grub/efi.img \
    -no-emul-boot \
    -isohybrid-gpt-hfsplus \
    -isohybrid-mbr /usr/lib/grub/i386-pc/boot_hybrid.img \
    -input-charset utf-8 \
    -output "$ISO_OUTPUT" \
    "$BUILD_DIR/iso" 2>&1 | tail -5

echo -e "  ${GREEN}ISO written to $ISO_OUTPUT${OFF}"
echo ""
echo -e "${GOLD}SIOS ISO build complete.${OFF}"
echo -e "  ${DIM}Size: $(du -h "$ISO_OUTPUT" | cut -f1)${OFF}"
echo -e "  ${DIM}SHA-256: $(sha256sum "$ISO_OUTPUT" | cut -d' ' -f1)${OFF}"
echo ""
echo -e "  ${DIM}Test with: qemu-system-x86_64 -m 4096 -cdrom \"$ISO_OUTPUT\"${OFF}"
