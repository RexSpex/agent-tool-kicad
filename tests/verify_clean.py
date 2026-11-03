"""Route the acceptance board via live MCP and export review/manufacturing files."""
import json
import sys
from pathlib import Path
from client import Client
c = Client(sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:48322')
board = '/workspace/led-demo/led-demo.kicad_pcb'
sch = '/workspace/led-demo/led-demo.kicad_sch'
exports = '/workspace/led-demo/exports/'
report = {}
Path('.evidence').mkdir(exist_ok=True)

def call(name, **arguments):
    result = c.call(name, **arguments)
    report.setdefault(name, []).append(result)
    Path('.evidence/route-report.json').write_text(json.dumps(report, indent=2))
    print(name, json.dumps(result)[:600], flush=True)
    return result

call('run_erc', schematic=sch, output='/workspace/led-demo/erc.json')
call('save_project')
r = call('run_drc', board=board, sync_live_board=True, output='/workspace/led-demo/drc.json')
assert r['errors'] == 0 and r['warnings'] == 0 and r['unconnected_items'] == 0 and r['schematic_parity'] == 0, r
call('export_gerber', board=board, output_dir=exports+'gerbers')
call('export_pdf', board=board, output=exports+'led-demo.pdf', layers=['F.Cu','F.SilkS','Edge.Cuts'])
call('export_svg', board=board, output=exports+'led-demo.svg', layers=['F.Cu','F.SilkS','Edge.Cuts'])
call('export_schematic_pdf', schematic=sch, output=exports+'schematic.pdf')
call('render_schematic_png', schematic=sch, output=exports+'schematic.png', width_px=1600)
print('Clean-board MCP checks and refreshed exports pass')
