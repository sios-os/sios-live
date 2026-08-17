#!/bin/bash
# finish-iso.sh — Complete the ISO build from the squashfs step.
# Assumes the rootfs is already built at /tmp/sios-iso-build/rootfs.

BUILD=/tmp/sios-iso-build
OUTPUT=/mnt/d/SIOS-Build/sios-live/sios-ubuntu-24.04.iso

# Unmount chroot
umount -lf "$BUILD/rootfs/dev" 2>/dev/null || true
umount -lf "$BUILD/rootfs/proc" 2>/dev/null || true
umount -lf "$BUILD/rootfs/sys" 2>/dev/null || true
umount -lf "$BUILD/rootfs/run" 2>/dev/null || true

# Step 4: squashfs with gzip (fast)
echo "=== Step 4: squashfs ==="
mkdir -p "$BUILD/iso/casper"
rm -f "$BUILD/iso/casper/filesystem.squashfs"
mksquashfs "$BUILD/rootfs" "$BUILD/iso/casper/filesystem.squashfs" -comp gzip -no-progress -quiet
echo "Squashfs: $(ls -lh "$BUILD/iso/casper/filesystem.squashfs" | awk '{print $5}')"

# Step 5: boot structure
echo "=== Step 5: boot structure ==="
cp "$BUILD/rootfs"/boot/vmlinuz-* "$BUILD/iso/casper/vmlinuz"
cp "$BUILD/rootfs"/boot/initrd.img-* "$BUILD/iso/casper/initrd"

# GRUB i386 boot image
mkdir -p "$BUILD/iso/boot/grub/i386-pc"
grub-mkimage -o "$BUILD/iso/boot/grub/i386-pc/eltorito.img" \
    -O i386-pc-eltorito -p /boot/grub \
    biosdisk iso9660 linux ls cat echo reboot halt search normal

# GRUB EFI boot image
mkdir -p "$BUILD/iso/EFI/BOOT"
grub-mkimage -o "$BUILD/iso/EFI/BOOT/bootx64.efi" \
    -O x86_64-efi -p /boot/grub \
    iso9660 linux ls cat echo reboot halt search normal

# GRUB config
cat > "$BUILD/iso/boot/grub/grub.cfg" << 'GRUBCFG'
set default=0
set timeout=5
set menu_color_normal="white/black"
set menu_color_highlight="yellow/black"
set color_normal="light-gray/black"
set color_highlight="yellow/black"

menuentry "SIOS - Sovereign Interactive Operating System" {
    linux /casper/vmlinuz boot=casper quiet splash ---
    initrd /casper/initrd
}

menuentry "SIOS - Safe Mode (no splash)" {
    linux /casper/vmlinuz boot=casper nomodeset ---
    initrd /casper/initrd
}

menuentry "SIOS - Recovery Console" {
    linux /casper/vmlinuz boot=casper single ---
    initrd /casper/initrd
}
GRUBCFG

# .disk/info
mkdir -p "$BUILD/iso/.disk"
echo "SIOS Ubuntu 24.04 - Sovereign Interactive Operating System" > "$BUILD/iso/.disk/info"

# README
cat > "$BUILD/iso/README.txt" << 'README'
SIOS - Sovereign Interactive Operating System
=============================================

Live bootable ISO built on Ubuntu 24.04 with the SIOS spatial desktop.

Boot it to enter the SIOS environment. Default login: sios / sios

Includes:
  - ANUBIS self-development runtime (Python)
  - SIOS spatial desktop (Godot 4)
  - Constitutional kernel and evidence ledger
  - Sandboxed code execution
  - LightDM greeter with SIOS branding
  - Plymouth boot splash

Note: llama3.1:8b model is NOT on the ISO (too large).
After boot, install Ollama and pull the model:
  curl -fsSL https://ollama.com/install.sh | sh
  ollama pull llama3.1:8b
README

echo "Boot structure done"

# Step 6: ISO
echo "=== Step 6: building ISO ==="
xorriso -as mkisofs \
    -r -V "SIOS Ubuntu 24.04" \
    -b boot/grub/i386-pc/eltorito.img \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    -input-charset utf-8 \
    -output "$OUTPUT" \
    "$BUILD/iso" 2>&1 | tail -10

echo ""
echo "=== Complete ==="
ls -lh "$OUTPUT"
sha256sum "$OUTPUT"
