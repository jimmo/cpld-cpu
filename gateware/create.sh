#!/bin/bash

set -e

mkdir -p $1
cat ioregister/ioregister.vhd | sed "s/ioregister/$1/g" > $1/$1.vhd
cp ioregister/ioregister.ucf $1/$1.ucf
