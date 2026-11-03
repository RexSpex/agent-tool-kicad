"""Build local CAD service, select available loopback port, run acceptance check."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SERVICE = 'kicad'
PREFIX = 'KICAD'
DEFAULT_PORT = 48322

def run(*args, capture=False, env=None):
    return subprocess.run(args, cwd=ROOT, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None, env=env)

def available(port):
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def set_port(path, port):
    original = path.read_text() if path.exists() else ""
    key = PREFIX + "_PORT"
    pattern = re.compile(r"(?m)^\s*(?:export\s+)?" + key + r"\s*=.*$")
    updated = pattern.sub(key + "=" + str(port), original)
    if updated == original and not pattern.search(original):
        updated = original + ("\n" if original and not original.endswith("\n") else "") + key + "=" + str(port) + "\n"
    if updated != original:
        path.write_text(updated)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, help="Require this host port; fail if occupied")
    args = parser.parse_args()
    if args.port is not None and not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if not shutil.which("docker"):
        raise RuntimeError("Install Docker with Compose v2 and start Docker first.")
    if shutil.disk_usage(ROOT).free < 12 * 1024**3:
        raise RuntimeError("Free at least 12 GiB on host disk before building Docker image.")
    system = json.loads(run("docker", "info", "--format", "{{json .}}", capture=True).stdout)
    if system["OSType"] != "linux":
        raise RuntimeError("Switch Docker to Linux containers first.")
    run("docker", "compose", "version", capture=True)
    config = json.loads(run("docker", "compose", "config", "--format", "json", capture=True).stdout)
    service = config["services"][SERVICE]
    binding = service["ports"][0]
    if binding.get("host_ip") != "127.0.0.1":
        raise RuntimeError("Setup requires loopback binding 127.0.0.1. Review local Compose settings.")
    port = args.port or int(binding.get("published") or DEFAULT_PORT)
    running = run("docker", "compose", "ps", "--status", "running", "--quiet", SERVICE, capture=True).stdout.strip()
    owned_port = None
    if running:
        container = json.loads(run("docker", "inspect", running, capture=True).stdout)[0]
        ports = container["NetworkSettings"]["Ports"].get("8080/tcp") or []
        owned_port = next((int(item["HostPort"]) for item in ports if item["HostIp"] == "127.0.0.1"), None)
    if not available(port) and port != owned_port:
        if args.port or os.environ.get(PREFIX + "_PORT"):
            raise RuntimeError(f"Port {port} is occupied. Select another port with --port.")
        for candidate in range(DEFAULT_PORT, DEFAULT_PORT + 100):
            if available(candidate):
                port = candidate
                break
        else:
            raise RuntimeError("No free port in preferred range. Select --port explicitly.")
    set_port(ROOT / ".env", port)
    env = dict(os.environ, **{PREFIX + "_PORT": str(port)})
    run("docker", "compose", "up", "-d", "--build", "--wait", "--wait-timeout", "300", env=env)
    origin = f"http://localhost:{port}"
    run(sys.executable, "tests/smoke.py", origin)
    print(f"Desktop: {origin}/\nMCP: {origin}/mcp\nPort saved in {ROOT / '.env'}")
    print("Configure this MCP URL in your agent harness. See AGENT_PROMPT.md.")

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
