"""Small standard-library MCP client used by acceptance checks."""
import json
import urllib.request

class Client:
    def __init__(self, origin):
        self.origin = origin.rstrip('/')
        self.sequence = 0
        self.rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                              'clientInfo': {'name': 'agent-tool-kicad-acceptance', 'version': '1'}})
        self.rpc('notifications/initialized', {}, notify=True)

    def rpc(self, method, params, notify=False):
        self.sequence += 1
        payload = {'jsonrpc': '2.0', 'method': method, 'params': params}
        if not notify:
            payload['id'] = self.sequence
        req = urllib.request.Request(self.origin + '/mcp', data=json.dumps(payload).encode(),
                                    headers={'Content-Type': 'application/json',
                                             'Accept': 'application/json, text/event-stream'})
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read()
        if notify:
            return None
        reply = json.loads(raw)
        if 'error' in reply:
            raise RuntimeError(reply['error'])
        return reply['result']

    def call(self, name, **arguments):
        result = self.rpc('tools/call', {'name': name, 'arguments': arguments})
        values = []
        for block in result.get('content', []):
            if block['type'] == 'text':
                try:
                    values.append(json.loads(block['text']))
                except ValueError:
                    values.append(block['text'])
        if result.get('isError'):
            raise RuntimeError(f'{name}: {values}')
        for v in values:
            if isinstance(v, dict) and v.get('success') is False:
                raise RuntimeError(f'{name}: {v}')
        return values[0] if len(values) == 1 else values

if __name__ == '__main__':
    import sys
    c = Client(sys.argv[1])
    print(json.dumps(c.call(sys.argv[2], **json.loads(sys.argv[3] if len(sys.argv) > 3 else '{}')), indent=2))
