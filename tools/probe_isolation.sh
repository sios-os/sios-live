#!/usr/bin/env bash
# Probe what real OS-level isolation primitives are available for the sandbox.
set -uo pipefail

echo "=== tooling ==="
for t in bwrap unshare nsenter setpriv timeout; do
  if command -v "$t" >/dev/null 2>&1; then
    echo "  $t: present  ($(command -v "$t"))"
  else
    echo "  $t: MISSING"
  fi
done

echo "=== namespace sysctls ==="
for f in /proc/sys/user/max_user_namespaces /proc/sys/kernel/unprivileged_userns_clone; do
  if [ -r "$f" ]; then echo "  $f = $(cat "$f")"; else echo "  $f = n/a"; fi
done

echo "=== can we unshare a network namespace? ==="
if unshare --net --fork --pid true 2>/dev/null; then
  echo "  privileged unshare --net: WORKS"
else
  echo "  privileged unshare --net: FAILS"
fi

echo "=== rootless userns + net unshare? ==="
if unshare --user --map-root-user --net true 2>/dev/null; then
  echo "  rootless userns+net: WORKS"
else
  echo "  rootless userns+net: FAILS"
fi

echo "=== verify network is actually dead inside the namespace ==="
# The real test: confirm outbound access fails inside, succeeds outside.
if unshare --net --fork --pid \
     sh -c 'curl -s --max-time 4 -o /dev/null http://1.1.1.1 && echo LEAK || echo blocked' 2>/dev/null \
     | grep -q blocked; then
  echo "  network inside ns: BLOCKED (good)"
else
  echo "  network inside ns: could not confirm blocked"
fi

echo "=== RLIMIT enforcement check (address space) ==="
python3 - <<'PY'
import resource, subprocess, sys

def child():
    # 256 MB address-space cap; a 512 MB allocation must fail.
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)

r = subprocess.run(
    [sys.executable, "-c", "b = bytearray(512*1024*1024); print('ALLOCATED')"],
    preexec_fn=child, capture_output=True, text=True, timeout=30,
)
if "ALLOCATED" in r.stdout:
    print("  RLIMIT_AS: NOT enforced (allocation succeeded)")
else:
    print("  RLIMIT_AS: enforced (allocation refused)")
PY

echo "=== DONE ==="
