import json
from pathlib import Path
root = Path('/home/cad/.config/kicad/10.0')
f = root / 'kicad_common.json'
data = json.loads(f.read_text()) if f.exists() else {}
data.setdefault('api', {})['enable_server'] = True
data.setdefault('do_not_show_again', {}).update(update_check_prompt=True, data_collection_prompt=True)
f.write_text(json.dumps(data, indent=2))
# Do not replace user projects. Initial blank board supports first-run GUI and API.
project = Path('/workspace/led-demo')
project.mkdir(exist_ok=True)
p = project / 'led-demo.kicad_pro'
if not p.exists():
    p.write_text('{}\n')
board = project / 'led-demo.kicad_pcb'
if not board.exists():
    import pcbnew
    pcbnew.SaveBoard(str(board), pcbnew.BOARD())

# First-run library selection must not block an unattended desktop.
import shutil
for name in ('sym-lib-table', 'fp-lib-table'):
    target = root / name
    template = Path('/usr/share/kicad/template') / name
    if not target.exists() and template.exists():
        shutil.copyfile(template, target)

blocks = root / 'design-block-lib-table'
if not blocks.exists():
    blocks.write_text('(design_block_lib_table (version 1))\n')
