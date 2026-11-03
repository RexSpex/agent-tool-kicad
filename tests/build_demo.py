"""Create LED acceptance design through MCP. Requires untouched first-run demo."""
import json
import sys
from pathlib import Path
from client import Client

c = Client(sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:48322')
sch = '/workspace/led-demo/led-demo.kicad_sch'
board = '/workspace/led-demo/led-demo.kicad_pcb'
report = {}
Path('.evidence').mkdir(exist_ok=True)

def call(name, **args):
    result = c.call(name, **args)
    report.setdefault(name, []).append(result)
    Path('.evidence/demo-report.json').write_text(json.dumps(report, indent=2))
    print(name, json.dumps(result)[:800], flush=True)
    return result

call('create_schematic', path=sch)
for ref, lib, value, footprint, x, y, rotation in [
    ('J1', 'Connector_Generic:Conn_01x02', '5V INPUT', 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', 100.33, 100.33, 0),
    ('R1', 'Device:R', '330', 'Resistor_SMD:R_0805_2012Metric', 120.65, 100.33, 90),
    ('D1', 'Device:LED', 'RED', 'LED_SMD:LED_0805_2012Metric', 140.97, 100.33, 180),
]:
    call('add_schematic_component', schematic=sch, reference=ref, lib_id=lib,
         value=value, footprint=footprint, x=x, y=y, rotation=rotation)
# Exercise real ERC failures before wiring rather than trusting an empty report.
before = call('run_erc', schematic=sch, output='/workspace/led-demo/erc-before.json')
assert before['errors'] > 0, before
for ref, pin, net in [('J1','1','VIN'), ('R1','1','VIN'), ('R1','2','LED_A'),
                      ('D1','2','LED_A'), ('D1','1','GND'), ('J1','2','GND')]:
    call('connect_to_net', schematic=sch, reference=ref, pin_number=pin, net=net)
after = call('run_erc', schematic=sch, output='/workspace/led-demo/erc.json')
assert after['errors'] == 0 and after['warnings'] == 0, after
call('generate_netlist', schematic=sch, output='/workspace/led-demo/led-demo.net')
plan = call('update_pcb_from_schematic', schematic=sch, board=board)
call('update_pcb_from_schematic', schematic=sch, board=board, dry_run=False,
     expected_plan_revision=plan['plan_revision'])
call('set_board_size', board=board, width=25, height=17, origin_x=100, origin_y=100)
for ref, x, y, rotation in [('J1',105,105,0), ('R1',110,105,0), ('D1',115,105,180)]:
    call('move_component', board=board, reference=ref, x=x, y=y)
    call('rotate_component', board=board, reference=ref, rotation=rotation)
refresh = call('update_footprints_from_library', board=board)
assert refresh['status'] == 'ready', refresh
call('update_footprints_from_library', board=board, dry_run=False, expected_plan_revision=refresh['plan_revision'])
call('save_project')
before = call('run_drc', board=board, sync_live_board=True, output='/workspace/led-demo/drc-before.json')
assert before['unconnected_items'] > 0, before
# Actual pad positions come from IPC, avoiding assumptions about footprint origins.
pads = {}
for ref in ['J1','R1','D1']:
    pads[ref] = call('get_component_pads', board=board, reference=ref)
    assert pads[ref]['source'] == 'ipc', pads[ref]
print('PAD_DATA', json.dumps(pads), flush=True)
# Subsequent routing is completed by tests/route_demo.py after inspecting IPC pad data.
with open('.evidence/demo-report.json', 'w') as f:
    json.dump(report, f, indent=2)
