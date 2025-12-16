#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"

export PYTHONPATH="$HERE/../share/creative-suite"
exec python3 "$HERE/../share/creative-suite/src/main.py"

