#!/usr/bin/env bash
# Remove tamper residue left by sandbox-escape tests that ran before the
# mount-masking fix landed. Verifies the file still parses afterwards.
set -euo pipefail

ROOT=/mnt/d/SIOS-Build/sios-live
TARGET="$ROOT/anubis/constitution.py"

echo "before: $(grep -c '^# tampered$' "$TARGET" || true) tamper line(s)"
sed -i '/^# tampered$/d' "$TARGET"
echo "after : $(grep -c '^# tampered$' "$TARGET" || true) tamper line(s)"

rm -f /etc/anubis-breach

python3 -c "import ast,sys; ast.parse(open('$TARGET').read()); print('constitution.py parses cleanly')"
