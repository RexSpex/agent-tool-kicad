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

pads = {}
for ref in ['J1', 'R1', 'D1']:
    r = call('get_component_pads', board=board, reference=ref)
    assert r['source'] == 'ipc', r
    pads[ref] = {p['number']: p for p in r['pads']}
def point(ref, number):
    p = pads[ref][number]
    return (p['x'], p['y'])
def route(net, points):
    for (x1,y1),(x2,y2) in zip(points,points[1:]):
        call('route_trace', board=board, net_name=net, layer='F.Cu',
             x1=x1,y1=y1,x2=x2,y2=y2,width=0.25)
route(pads['J1']['1']['net'], [point('J1','1'),point('R1','1')])
route(pads['R1']['2']['net'], [point('R1','2'),point('D1','2')])
route(pads['D1']['1']['net'], [point('D1','1'),(118,105),(118,112),(105,112),point('J1','2')])
call('save_project')
r = call('run_drc', board=board, sync_live_board=True, output='/workspace/led-demo/drc.json')
assert r['errors'] == 0 and r['unconnected_items'] == 0, r
call('export_gerber', board=board, output_dir=exports+'gerbers')
call('export_pdf', board=board, output=exports+'led-demo.pdf', layers=['F.Cu','F.SilkS','Edge.Cuts'])
call('export_svg', board=board, output=exports+'led-demo.svg', layers=['F.Cu','F.SilkS','Edge.Cuts'])
call('export_schematic_pdf', schematic=sch, output=exports+'schematic.pdf')
call('render_schematic_png', schematic=sch, output=exports+'schematic.png', width_px=1600)
print('Routing and export acceptance pass; inspect reported warnings separately.')
