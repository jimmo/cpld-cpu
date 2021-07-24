#!/bin/bash

set -e

DIR=`readlink -m "$0"`
DIR=`dirname "$DIR"`
SRC=`readlink -m "$2"`

pushd "$DIR/../pysim"
source .venv/bin/activate
python3 -m cpu_ax_13.asm "$SRC" /tmp/data.py
deactivate
popd

~/src/github.com/micropython/micropython/tools/pyboard.py --device $1 "$DIR/main.py" /tmp/data.py
