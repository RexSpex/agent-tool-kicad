"""Call local Streamable HTTP MCP from any agent with terminal access."""
import argparse
import json
import sys
import urllib.request

def failed(value):
    if isinstance(value, dict):
        return value.get("isError", False) or value.get("success") is False or any(failed(item) for item in value.values())
    if isinstance(value, list):
        return any(failed(item) for item in value)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            return False
        return failed(decoded) if isinstance(decoded, (dict, list)) else False
    return False

class Client:
    def __init__(self, url):
        self.url = url.rstrip("/")
        self.session = None
        self.protocol = None
        self.sequence = 0
        initialized = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                               "clientInfo": {"name": "local-cad-client", "version": "1"}})
        self.protocol = initialized["protocolVersion"]
        self.rpc("notifications/initialized", {}, notify=True)

    def rpc(self, method, params, notify=False):
        self.sequence += 1
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notify:
            message["id"] = self.sequence
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        if self.protocol:
            headers["MCP-Protocol-Version"] = self.protocol
        request = urllib.request.Request(self.url, data=json.dumps(message).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=180) as response:
            self.session = response.headers.get("Mcp-Session-Id", self.session)
            raw = response.read().decode()
        if notify:
            return None
        replies = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith("data: ")]
        if not replies:
            replies = [json.loads(raw)]
        for reply in replies:
            if reply.get("id") == self.sequence:
                if "error" in reply:
                    raise RuntimeError(reply["error"])
                return reply["result"]
        raise RuntimeError("Missing JSON-RPC response")

    def close(self):
        if self.session:
            request = urllib.request.Request(self.url, method="DELETE", headers={"Mcp-Session-Id": self.session, "MCP-Protocol-Version": self.protocol})
            try:
                with urllib.request.urlopen(request, timeout=10):
                    pass
            except OSError:
                pass

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:48322/mcp")
    parser.add_argument("action", choices=["list", "call"])
    parser.add_argument("name", nargs="?")
    parser.add_argument("arguments", nargs="?", default="{}", help="JSON object or @path/to/arguments.json")
    args = parser.parse_args()
    client = Client(args.url)
    try:
        if args.action == "list":
            result = client.rpc("tools/list", {})
            while result.get("nextCursor"):
                page = client.rpc("tools/list", {"cursor": result["nextCursor"]})
                result["tools"].extend(page["tools"])
                result["nextCursor"] = page.get("nextCursor")
        else:
            if not args.name:
                parser.error("call requires tool name")
            value = args.arguments
            if value.startswith("@"):
                from pathlib import Path
                value = Path(value[1:]).read_text()
            arguments = json.loads(value)
            if not isinstance(arguments, dict):
                parser.error("tool arguments must be a JSON object")
            result = client.rpc("tools/call", {"name": args.name, "arguments": arguments})
        print(json.dumps(result, indent=2))
        if args.action == "call" and failed(result):
            sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()
