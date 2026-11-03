import sys

from client import Client


origin = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:48322").rstrip("/")
result = Client(origin).call(
    "check_freerouting", jar_path="/opt/freerouting/freerouting.jar"
)

assert result["engine_found"], result
assert result["java_available"], result
assert result["native_mcp_available"], result
assert result["bridge_available"], result
assert result["native_mcp_tool_count"] >= 6, result
print(
    "FreeRouting native MCP pass:",
    result["native_mcp_tool_count"],
    "tools, protocol",
    result["server_protocol_version"],
)
