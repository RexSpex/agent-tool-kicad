import pathlib
import socket
import urllib.request

for port in (5900, 6080, 8000, 8080):
    with socket.create_connection(("127.0.0.1", port), timeout=3):
        pass
assert pathlib.Path("/tmp/.X11-unix/X0").exists()
with urllib.request.urlopen("http://127.0.0.1:8080/healthz", timeout=3) as response:
    assert response.status == 200

with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3) as response:
    assert response.read() == b"ok"

assert pathlib.Path('/tmp/kicad/api.sock').is_socket()

# A socket can exist while KiCad is blocked behind a modal dialog.
import json
payload = {'jsonrpc':'2.0', 'id':1, 'method':'tools/call',
           'params':{'name':'open_project', 'arguments':{}}}
request = urllib.request.Request('http://127.0.0.1:8000/mcp', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request, timeout=7) as response:
    result = json.load(response)
state = json.loads(result['result']['content'][0]['text'])
assert state['ipc_available'] and state['open_board_count'] >= 1, 'PCB IPC is not ready'
