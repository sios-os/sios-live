#!/bin/bash
# copy-shots.sh — Copy screenshots from Godot user dir to the desktop folder.
DIR="/root/.local/share/godot/app_userdata/SIOS Desktop"
DST="/mnt/d/SIOS-Build/sios-live/desktop"
for f in shot-hub shot-workspace shot-forge shot-observatory shot-command; do
    cp "$DIR/$f.png" "$DST/$f.png"
done
ls -la "$DST"/shot-*.png
