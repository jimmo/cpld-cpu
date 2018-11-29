This exactly implements the CPU from https://github.com/cpldcpu/MCPU

The simulator is written to match the VHDL as closely as possible.

I've added an assembler that generates the same machine code, including the macro ops described such as `sub`, etc plus a few more. Additionally, the assembler automatically generates some useful constant values at known locations, such as `one`, `allones`, etc, and a simple memory-mapped output interface.

There are three demos:
 - tests/count.s -- demonstrates counting up and down with output
 - tests/mem.s -- uses self-modifying code to fill RAM with a sequence
 - tests/prime.s -- copied from https://jeelabs.org/2017/11/tfoc---a-minimal-computer/
 
