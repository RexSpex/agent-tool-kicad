"""Verify JSON/SSE negotiation and nested tool error handling."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("mcp_client", Path(__file__).resolve().parents[1] / "scripts/mcp.py")
mcp_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_client)

class Response:
    def __init__(self, body):
        self.body = body.encode()
        self.headers = {"Mcp-Session-Id": "unit-session"}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self):
        return self.body

class ClientTests(unittest.TestCase):
    def test_negotiated_protocol_and_session_survive_sse(self):
        responses = [
            Response(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-06-18"}})),
            Response(""),
            Response('event: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n'
                     'event: message\ndata: {"jsonrpc":"2.0","id":3,"result":{"tools":[]}}\n\n'),
            Response(""),
        ]
        with patch.object(mcp_client.urllib.request, "urlopen", side_effect=responses) as opened:
            client = mcp_client.Client("http://localhost:49000/mcp")
            self.assertEqual(client.rpc("tools/list", {}), {"tools": []})
            client.close()
            request = opened.call_args_list[2].args[0]
            self.assertEqual(request.get_header("Mcp-session-id"), "unit-session")
            self.assertEqual(request.get_header("Mcp-protocol-version"), "2025-06-18")
            self.assertEqual(opened.call_args_list[3].args[0].method, "DELETE")

    def test_nested_tool_error_is_failure(self):
        result = {"content": [{"type": "text", "text": json.dumps([json.dumps({"success": False})])}]}
        self.assertTrue(mcp_client.failed(result))
        self.assertFalse(mcp_client.failed({"content": [{"type": "text", "text": '{"success":true}'}]}))

if __name__ == "__main__":
    unittest.main()
