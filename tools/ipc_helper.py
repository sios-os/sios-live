#!/usr/bin/env python3
"""ipc_helper.py — Bridge between Godot and the ANUBIS daemon socket.

Usage: python3 ipc_helper.py <request_json_file> <response_json_file>

Godot calls this via OS.execute(). It reads a JSON request from the input
file, sends it to the ANUBIS daemon over the Unix socket, and writes the
response to the output file.
"""
import json
import os
import socket
import sys

SOCKET_PATH = os.environ.get("ANUBIS_SOCKET", "/tmp/anubis.sock")

def main():
    if len(sys.argv) < 3:
        print("Usage: ipc_helper.py <req_file> <resp_file>", file=sys.stderr)
        sys.exit(1)
    req_file = sys.argv[1]
    resp_file = sys.argv[2]

    # Read request
    with open(req_file) as f:
        req_data = f.read()

    # Connect to daemon
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(SOCKET_PATH)
    except (FileNotFoundError, ConnectionRefusedError) as exc:
        with open(resp_file, "w") as f:
            json.dump({"error": f"cannot connect: {exc}"}, f)
        sys.exit(1)

    # Send request
    s.sendall((req_data + "\n").encode())

    # Read response
    try:
        resp = s.recv(65536).decode()
    except socket.timeout:
        resp = json.dumps({"error": "timeout"})
    s.close()

    # Write response
    with open(resp_file, "w") as f:
        f.write(resp)

if __name__ == "__main__":
    main()
