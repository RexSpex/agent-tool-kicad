"""Independent KiCad readback; run with container's Python after saving/recreation."""
import json
import hashlib
from pathlib import Path
import pcbnew

root = Path('/workspace/led-demo')
board = pcbnew.LoadBoard(str(root / 'led-demo.kicad_pcb'))
footprints = {f.GetReference(): f for f in board.GetFootprints()}
assert set(footprints) == {'J1', 'R1', 'D1'}, set(footprints)
expected = {'J1': {'1':'VIN','2':'GND'}, 'R1': {'1':'VIN','2':'LED_A'}, 'D1': {'1':'GND','2':'LED_A'}}
for ref, footprint in footprints.items():
    actual = {p.GetNumber(): p.GetNetname().removeprefix('/') for p in footprint.Pads()}
    assert actual == expected[ref], (ref, actual)
assert len(list(board.GetTracks())) >= 5
bounds = board.GetBoardEdgesBoundingBox()
assert abs(pcbnew.ToMM(bounds.GetWidth()) - 25) <= 0.1
assert abs(pcbnew.ToMM(bounds.GetHeight()) - 17) <= 0.1
erc = json.loads((root / 'erc.json').read_text())
assert erc['errors'] == 0 and erc['warnings'] == 0, erc
drc = json.loads((root / 'drc.json').read_text())
assert drc['unconnected_items'] == [], drc
assert drc['schematic_parity'] == [], drc
assert drc['violations'] == [], drc
for ref, footprint in footprints.items():
    assert footprint.GetField('Description').GetText(), ref
for pad in footprints['R1'].Pads():
    assert pad.GetSize().x == 1025000 and pad.GetSize().y == 1400000
full_drc = json.loads((root / 'drc-full.json').read_text())
assert all(full_drc[k] == [] for k in ('violations','unconnected_items','schematic_parity'))
full_erc = json.loads((root / 'erc-full.json').read_text())
assert all(not sheet['violations'] for sheet in full_erc['sheets'])
receipt = json.loads((root / 'clean-receipt.json').read_text())
assert receipt['rules_unchanged'] and receipt['placement_routing_nets_unchanged']
assert hashlib.sha256((root/'led-demo.kicad_pcb').read_bytes()).hexdigest() == receipt['board_sha256']
for filename in ['led-demo.pdf', 'led-demo.svg', 'schematic.pdf', 'schematic.png']:
    assert (root / 'exports' / filename).stat().st_size > 100, filename
files = list((root / 'exports' / 'gerbers').glob('*'))
assert len(files) >= 8, [p.name for p in files]
assert any(p.suffix == '.drl' for p in files)
print(json.dumps({'footprints': sorted(footprints), 'tracks': len(list(board.GetTracks())),
                  'nets': expected, 'board_mm': [25,17], 'gerber_files': len(files),
                  'erc_errors': 0, 'drc_errors': 0, 'unconnected_items': 0,
                  'erc_warnings': 0, 'drc_warnings': 0, 'schematic_parity_warnings': 0, 'saved_readback': 'pass'}))
