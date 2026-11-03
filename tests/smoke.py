import base64, json, os, socket, ssl, sys, urllib.request, uuid
from urllib.parse import urlparse
origin = (sys.argv[1] if len(sys.argv)>1 else "http://localhost:48322").rstrip("/")
with urllib.request.urlopen(origin + "/", timeout=15) as response:
    assert response.status == 200
    assert response.url.startswith(origin + "/vnc.html?"), response.url
with urllib.request.urlopen(origin + "/vnc.html", timeout=15) as response:
    assert response.status == 200
address=urlparse(origin)
port=address.port or (443 if address.scheme=="https" else 80)
conn=socket.create_connection((address.hostname,port),timeout=15)
if address.scheme=="https":
    conn=ssl.create_default_context().wrap_socket(conn,server_hostname=address.hostname)
with conn:
    key=base64.b64encode(os.urandom(16)).decode()
    headers=f"GET /websockify HTTP/1.1\r\nHost: {address.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: binary\r\n\r\n"
    conn.sendall(headers.encode())
    data=conn.recv(4096)
    assert b"101 Switching Protocols" in data, data[:200]
    if b"RFB " not in data:
        data+=conn.recv(4096)
    assert b"RFB 003.008" in data, data[:200]
print("Desktop redirect and VNC handshake pass")
from client import Client
client = Client(origin)
names = {t['name'] for t in client.rpc('tools/list', {})['tools']}
assert {'list_toolboxes', 'load_toolset', 'get_installation_info'} <= names
info = client.call('get_installation_info')
print('MCP initialize and tool discovery pass')
assert info['build']['version'] == '0.13.0', info['build']
assert info['kicad']['version'].startswith('10.'), info['kicad']
print('Versions:', info['build']['version'], info['kicad']['version'])
state = client.call('open_project', path='/workspace/led-demo/led-demo.kicad_pcb')
assert state['ipc_available'] and state['requested_open'], state
print('Target PCB open over live IPC')
try:
    req = urllib.request.Request(origin + '/mcp', data=b'{}', headers={'Content-Type':'application/json', 'Origin':'https://untrusted.example'})
    urllib.request.urlopen(req, timeout=5)
    raise AssertionError('Foreign Origin accepted')
except urllib.error.HTTPError as error:
    assert error.code == 403
print('Foreign MCP Origin rejected')
