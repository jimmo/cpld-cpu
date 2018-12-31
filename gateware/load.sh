#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 dirname"
    exit 1
fi

JED="$1.jed"

scp $1/$JED pi@192.168.200.1:/tmp/$JED
ssh pi@192.168.200.1 sudo xc3sprog -v -c sysfsgpio -p 0 /tmp/$JED:w
