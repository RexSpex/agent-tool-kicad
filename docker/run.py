"""Hold exclusive workspace ownership for the full desktop process lifetime."""
import fcntl
import json
import runpy
import signal
import subprocess
from pathlib import Path

with open('/workspace/.agent-tool-kicad.owner', 'a') as owner:
    try:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Workspace already owned by another agent-tool-kicad container')
    runpy.run_path('/opt/bootstrap.py', run_name='__main__')
    # The demo belongs to this managed desktop. Docker replacement changes the
    # hostname, leaving KiCad's previous hostname lock behind. Never clear locks
    # elsewhere, or a lock written by a different user. Project bytes stay intact.
    for name in ('~led-demo.kicad_pcb.lck', '~led-demo.kicad_pro.lck'):
        path = Path('/workspace/led-demo') / name
        if path.exists():
            record = json.loads(path.read_text())
            if record.get('username') != 'cad':
                raise SystemExit('Demo lock belongs to a different user; inspect before reopening')
            path.unlink()
    process = subprocess.Popen(['/usr/bin/supervisord', '-c', '/opt/supervisord.conf'])
    def stop(signum, frame):
        process.send_signal(signum)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    raise SystemExit(process.wait())
