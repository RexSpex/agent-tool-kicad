#!/bin/sh
set -eu
mkdir -p /home/cad/.config/kicad/10.0 /home/cad/.fluxbox /tmp/runtime-cad
chmod 700 /tmp/runtime-cad
exec python3 /opt/run.py
