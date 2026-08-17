"""Run the VPN setup script on the IONOS VPS via SSH.

Uses the system ssh command via subprocess (no paramiko dependency).
Falls back to paramiko if the ssh command is not available.

Usage:
    python tools/run_vpn_setup.py

This is a one-time setup script. After the VPN is configured, you should:
    1. Change the root password on the VPS
    2. Disable password SSH auth (use keys only)
    3. Save the client config to /etc/wireguard/wg0.conf on the SIOS machine
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREDS_FILE = ROOT / "config" / "cloud_credentials.json"
SETUP_SCRIPT = ROOT / "tools" / "setup_vpn.sh"


def _ssh_via_subprocess(
    host: str, user: str, password: str, port: int,
    script_content: str,
) -> int:
    """Run a script on a remote host via the ssh command.

    Uses sshpass for password authentication if available.
    Falls back to ssh with key-based auth otherwise.
    """
    ssh_cmd = shutil.which("ssh")
    if not ssh_cmd:
        print("ERROR: ssh command not found. Install openssh-client.")
        return 1

    # Build the SSH command
    ssh_args = [
        ssh_cmd,
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
        f"{user}@{host}",
    ]

    # Check if sshpass is available for password auth
    sshpass = shutil.which("sshpass")
    if sshpass and password:
        # Use sshpass to provide the password
        cmd = [sshpass, "-p", password] + ssh_args
    elif not password:
        # No password — assume key-based auth
        cmd = ssh_args
    else:
        # Password provided but no sshpass
        print("WARNING: sshpass not found. Trying key-based auth.")
        print("If this fails, install sshpass: apt install sshpass")
        cmd = ssh_args

    # The script content is piped via stdin
    full_command = f"bash -s -- <<'SETUP_EOF'\n{script_content}\nSETUP_EOF"

    print("Connecting via ssh...")
    try:
        result = subprocess.run(
            cmd,
            input=full_command,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Print output
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")

        print()
        print(f"=== Script finished with exit code {result.returncode} ===")

        if result.returncode != 0:
            print("WARNING: script reported errors. Check output above.")

        return result.returncode

    except subprocess.TimeoutExpired:
        print("ERROR: SSH connection timed out")
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


def _ssh_via_paramiko(
    host: str, user: str, password: str, port: int,
    script_content: str,
) -> int:
    """Fallback: Run script via paramiko if ssh command unavailable.

    This is the legacy path, kept as a fallback for environments
    where the ssh command is not available but paramiko is installed.
    """
    try:
        import paramiko
    except ImportError:
        print("ERROR: neither ssh command nor paramiko available.")
        print("Install one of: openssh-client (preferred) or paramiko")
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host, port=port, username=user, password=password,
            timeout=30, allow_agent=False, look_for_keys=False,
        )
        print("Connected via paramiko. Running VPN setup script...")

        stdin, stdout, stderr = client.exec_command(
            f"bash -s -- <<'SETUP_EOF'\n{script_content}\nSETUP_EOF",
            timeout=300,
        )

        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096).decode("utf-8", "replace")
                print(chunk, end="")
            if stderr.channel.recv_stderr_ready():
                chunk = stderr.channel.recv_stderr(4096).decode("utf-8", "replace")
                print(chunk, end="")
            time.sleep(0.1)

        remaining = stdout.read().decode("utf-8", "replace")
        if remaining:
            print(remaining, end="")
        remaining_err = stderr.read().decode("utf-8", "replace")
        if remaining_err:
            print(remaining_err, end="")

        exit_code = stdout.channel.recv_exit_status()
        print()
        print(f"=== Script finished with exit code {exit_code} ===")
        return exit_code

    except paramiko.AuthenticationException:
        print("ERROR: authentication failed — check credentials")
        return 1
    except paramiko.SSHException as exc:
        print(f"ERROR: SSH connection failed: {exc}")
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        client.close()


def main() -> int:
    # Load credentials
    if not CREDS_FILE.exists():
        print(f"ERROR: credentials file not found: {CREDS_FILE}")
        return 1
    creds = json.loads(CREDS_FILE.read_text(encoding="utf-8"))
    vps = creds.get("ionos_vps", {})
    host = vps.get("host", "")
    user = vps.get("user", "root")
    password = vps.get("password", "")
    port = vps.get("port", 22)

    if not host:
        print("ERROR: missing IONOS VPS host in config")
        return 1

    # Load the setup script
    if not SETUP_SCRIPT.exists():
        print(f"ERROR: setup script not found: {SETUP_SCRIPT}")
        return 1
    script_content = SETUP_SCRIPT.read_text(encoding="utf-8")

    print(f"=== Connecting to {user}@{host}:{port} ===")
    print()

    # Try subprocess ssh first (no external Python dependency)
    ssh_cmd = shutil.which("ssh")
    if ssh_cmd:
        return _ssh_via_subprocess(host, user, password, port, script_content)
    else:
        # Fall back to paramiko
        return _ssh_via_paramiko(host, user, password, port, script_content)


if __name__ == "__main__":
    sys.exit(main())
