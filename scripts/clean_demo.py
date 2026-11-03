"""Repair only the two proven Konnect demo defects, with PCB Editor stopped.

Run in a one-off container against the same workspace. No rule changes.
A private candidate must pass full KiCad ERC/DRC before replacing the board.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import pcbnew

root = Path('/workspace/led-demo')
board_path = root / 'led-demo.kicad_pcb'
schematic = root / 'led-demo.kicad_sch'
project = root / 'led-demo.kicad_pro'
def run(*args):
    result = subprocess.run(['kicad-cli', *map(str, args)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
def identity(board):
    return {
        'footprints': sorted((f.GetReference(), f.m_Uuid.AsString(), f.GetPosition().x,
            f.GetPosition().y, f.GetOrientationDegrees(), f.GetFPID().GetLibItemName(),
            tuple(sorted((p.GetNumber(), p.m_Uuid.AsString(), p.GetPosition().x,
                p.GetPosition().y, p.GetNetname()) for p in f.Pads()))) for f in board.GetFootprints()),
        'tracks': sorted((t.m_Uuid.AsString(), t.GetStart().x, t.GetStart().y,
            t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.GetLayer(), t.GetNetname()) for t in board.GetTracks()),
        'outline': sorted((d.m_Uuid.AsString(), d.GetStart().x, d.GetStart().y,
            d.GetEnd().x, d.GetEnd().y, d.GetWidth(), d.GetLayer()) for d in board.GetDrawings()),
    }
with open('/workspace/.agent-tool-kicad.owner', 'a') as owner:
    fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
    original = board_path.read_bytes()
    protected = {p: p.read_bytes() for p in (schematic, project)}
    board = pcbnew.LoadBoard(str(board_path))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    assert set(footprints) == {'J1', 'R1', 'D1'}, 'Only the three-part acceptance demo is supported'
    before = identity(board)
    changes = []
    with tempfile.TemporaryDirectory(prefix='kicad-clean-') as temporary:
        candidate = Path(temporary)
        netlist = candidate / 'netlist.xml'
        run('sch', 'export', 'netlist', '--format', 'kicadxml', '--output', netlist, schematic)
        components = {c.attrib['ref']: c for c in ET.parse(netlist).findall('./components/comp')}
        for ref, footprint in footprints.items():
            description = components[ref].findtext('description') or ''
            assert description, f'Missing schematic description for {ref}'
            field = footprint.GetField('Description')
            if field.GetText() != description:
                assert field.GetText() == '', f'Refuse to replace nonempty Description on {ref}'
                field.SetText(description)
                changes.append({'reference': ref, 'field': 'Description', 'source': 'KiCad schematic netlist'})
        resistor = footprints['R1']
        assert resistor.GetFPID().GetLibItemName() == 'R_0805_2012Metric'
        library = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Resistor_SMD.pretty', 'R_0805_2012Metric')
        library_pads = {p.GetNumber(): p for p in library.Pads()}
        for pad in resistor.Pads():
            actual, expected = pad.GetSize(), library_pads[pad.GetNumber()].GetSize()
            assert actual.y == expected.y and expected.x - actual.x in (0, 1), 'Unexpected pad geometry; refuse repair'
            if actual.x != expected.x:
                changes.append({'reference':'R1', 'pad':pad.GetNumber(), 'width_nm_before':actual.x, 'width_nm_after':expected.x})
                pad.SetSize(expected)
        for path in protected:
            shutil.copyfile(path, candidate / path.name)
        output = candidate / board_path.name
        assert pcbnew.SaveBoard(str(output), board, True)
        assert identity(pcbnew.LoadBoard(str(output))) == before, 'Placement, routing, identity or nets changed'
        run('sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations',
            '--output', candidate/'erc-full.json', candidate/schematic.name)
        run('pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors',
            '--schematic-parity', '--exit-code-violations', '--output', candidate/'drc-full.json', output)
        drc = json.loads((candidate/'drc-full.json').read_text())
        assert all(drc[k] == [] for k in ('violations','unconnected_items','schematic_parity')), drc
        erc = json.loads((candidate/'erc-full.json').read_text())
        assert all(not sheet['violations'] for sheet in erc['sheets']), erc
        assert all(p.read_bytes() == value for p, value in protected.items()), 'Schematic or rules changed'
        assert board_path.read_bytes() == original, 'Board changed during repair'
        backup = root / '.repair-backups'
        backup.mkdir(exist_ok=True)
        digest = hashlib.sha256(original).hexdigest()
        backup_path = backup / (digest + '.kicad_pcb')
        if not backup_path.exists():
            backup_path.write_bytes(original)
        staged = root / '.clean-board.tmp'
        with staged.open('wb') as file:
            file.write(output.read_bytes()); file.flush(); os.fsync(file.fileno())
        os.replace(staged, board_path)
        for name in ('erc-full.json','drc-full.json'):
            shutil.copyfile(candidate/name, root/name)
        receipt = {'changes':changes, 'erc_errors':0, 'erc_warnings':0, 'drc_errors':0,
            'drc_warnings':0, 'unconnected_items':0, 'schematic_parity':0,
            'rules_unchanged':True, 'placement_routing_nets_unchanged':True,
            'backup_sha256':digest, 'board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest()}
        (root/'clean-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(receipt))
