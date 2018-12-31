#!/bin/bash

#set -x
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 dirname"
    exit 1
fi

VHD="$1/$1.vhd"
UCF="$1/$1.ucf"
XSVF="$1/$1.xsvf"
JED="$1/$1.jed"

if [ ! -f "$VHD" ]; then
    echo "$VHD not found."
    exit 1
fi

if [ ! -f "$UCF" ]; then
    echo "$UCF not found."
    exit 1
fi

VHD=$(readlink -m $VHD)
UCF=$(readlink -m $UCF)
XSVF=$(readlink -m $XSVF)
JED=$(readlink -m $JED)

echo "Building $VHD..."

BUILD=$(mktemp -d)
echo $BUILD

pushd $BUILD

mkdir tmp

cat > $1.prj <<EOF
vhdl work "$VHD"
EOF

cat > $1.xst <<EOF
set -tmpdir "tmp"
set -xsthdpdir "xst"
run
-ifn $1.prj
-ifmt mixed
-ofn $1
-ofmt NGC
-p xc9500xl
-top $1
-opt_mode Speed
-opt_level 1
-iuc NO
-keep_hierarchy Yes
-netlist_hierarchy As_Optimized
-rtlview Yes
-hierarchy_separator /
-bus_delimiter <>
-case Maintain
-verilog2001 YES
-fsm_extract YES -fsm_encoding Auto
-safe_implementation No
-mux_extract Yes
-resource_sharing YES
-iobuf YES
-pld_mp YES
-pld_xp YES
-pld_ce YES
-wysiwyg NO
-equivalent_register_removal YES
EOF

cat > make-xsvf.cmd <<EOF
setmode -bscan
setcable -p xsvf -file $XSVF
addDevice -p 1 -file $1.jed
program -e -v -p 1
quit
EOF

xst -intstyle xflow -ifn $1.xst -ofn $1.syr
ngdbuild -intstyle xflow -dd _ngo -uc $UCF -p xc9572xl-VQ44-10 $1.ngc $1.ngd
cpldfit -intstyle xflow -p xc9572xl-10-VQ44 -ofmt abel -optimize speed -loc on -slew fast -init low -inputs 54 -pterms 25 -unused float -power std -terminate keeper $1.ngd
cp $1.rpt ${VHD/.vhd/.rpt}
tsim -intstyle xflow $1 $1.nga
hprep6 -s IEEE1149 -n $1 -i $1
impact -batch make-xsvf.cmd
cp ${BUILD}/$1.jed $JED

popd
rm -rf $BUILD
