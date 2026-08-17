#!/bin/bash
# SIOS Plymouth theme — boot splash installer.
#
# Installs a minimal Plymouth theme that shows the SIOS hexagonal brand mark
# on a dark background during boot.

set -euo pipefail

THEME_DIR="/usr/share/plymouth/themes/sios"

mkdir -p "$THEME_DIR"

cat > "$THEME_DIR/sios.plymouth" << 'PLYMOUTH'
[Plymouth Theme]
Name=SIOS
Description=Sovereign Interactive Operating System boot splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/sios
ScriptFile=/usr/share/plymouth/themes/sios/sios.script
PLYMOUTH

cat > "$THEME_DIR/sios.script" << 'SCRIPT'
# SIOS Plymouth boot script
# Draws the hexagonal brand mark centered on a dark background with a
# gold progress indicator below it.

# ----------------------------------------------------------------- colors
bg_color = [0.012, 0.027, 0.051, 1.0];
gold_color = [0.769, 0.639, 0.353, 1.0];
gold_bright = [0.882, 0.780, 0.494, 1.0];
muted_color = [0.282, 0.306, 0.341, 1.0];

# ----------------------------------------------------------------- layout
screen_width = Window.GetWidth();
screen_height = Window.GetHeight();
center_x = screen_width / 2;
center_y = screen_height / 2;

# ----------------------------------------------------------------- hex mark
fun draw_hex(cx, cy, radius, color, line_width) {
    for (i = 0; i < 6; i++) {
        angle1 = (3.14159 * i / 3.0) + 0.5236;
        angle2 = (3.14159 * (i + 1) / 3.0) + 0.5236;
        x1 = cx + radius * Math.Cos(angle1);
        y1 = cy + radius * Math.Sin(angle1);
        x2 = cx + radius * Math.Cos(angle2);
        y2 = cy + radius * Math.Sin(angle2);
        Window.DrawLine(x1, y1, x2, y2, line_width, color);
    }
}

# ----------------------------------------------------------------- progress
progress = 0.0;
progress_bar_width = 200;
progress_bar_height = 2;

fun refresh_callback() {
    # Clear to background
    Window.SetBackgroundTopColor(bg_color);
    Window.SetBackgroundBottomColor(bg_color);

    # Draw outer hex
    draw_hex(center_x, center_y - 40, 50, gold_color, 2.0);

    # Draw inner hex
    draw_hex(center_x, center_y - 40, 35, gold_bright, 1.0);

    # Draw "S" placeholder (just a vertical line for now)
    Window.DrawLine(center_x - 8, center_y - 52, center_x - 8, center_y - 28, 2.0, gold_bright);
    Window.DrawLine(center_x - 8, center_y - 52, center_x + 8, center_y - 52, 2.0, gold_bright);
    Window.DrawLine(center_x + 8, center_y - 52, center_x + 8, center_y - 40, 2.0, gold_bright);
    Window.DrawLine(center_x + 8, center_y - 40, center_x - 8, center_y - 40, 2.0, gold_bright);
    Window.DrawLine(center_x - 8, center_y - 40, center_x - 8, center_y - 28, 2.0, gold_bright);
    Window.DrawLine(center_x - 8, center_y - 28, center_x + 8, center_y - 28, 2.0, gold_bright);

    # Title
    # (Plymouth script mode doesn't have text rendering without the label plugin;
    #  the hex mark alone is sufficient for brand identity during boot.)

    # Progress bar
    bar_y = center_y + 40;
    bar_x = center_x - progress_bar_width / 2;

    # Track
    Window.DrawLine(bar_x, bar_y, bar_x + progress_bar_width, bar_y, progress_bar_height, muted_color);

    # Filled portion
    filled = progress_bar_width * progress;
    if (filled > 0) {
        Window.DrawLine(bar_x, bar_y, bar_x + filled, bar_y, progress_bar_height, gold_color);
    }
}

Plymouth.SetRefreshFunction(refresh_callback);

# ----------------------------------------------------------------- boot progress
fun boot_progress_callback(duration, progress_value) {
    progress = progress_value;
}

Plymouth.SetBootProgressFunction(boot_progress_callback);

# ----------------------------------------------------------------- messages
fun message_callback(text) {
    # Show boot messages below the progress bar in muted color
    # (simplified — just update progress)
    progress = (progress + 0.05) * 0.5 + progress * 0.5;
}

Plymouth.SetMessageFunction(message_callback);
SCRIPT

# Create a simple logo as SVG (for reference / future use)
cat > "$THEME_DIR/logo.svg" << 'SVG'
<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" fill="#02070d"/>
  <polygon points="50,8 88,28 88,72 50,92 12,72 12,28" fill="none" stroke="#c4a35a" stroke-width="2"/>
  <polygon points="50,24 72,36 72,64 50,76 28,64 28,36" fill="none" stroke="#e1c77e" stroke-width="1"/>
  <text x="50" y="60" font-family="serif" font-size="36" fill="#e1c77e" text-anchor="middle">S</text>
</svg>
SVG

echo "SIOS Plymouth theme installed to $THEME_DIR"
echo "Enable with: plymouth-set-default-theme sios"
