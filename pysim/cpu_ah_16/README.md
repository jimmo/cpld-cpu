This is a more complicated design that allows for 8 registers and 16-bit memory addressing. It's loosely based on http://jaromir.xf.cz/fourbit/fourbit.html

The overall design is:
* 8-bit registers, 16-bit memory addressing.
* Fixed number of cycles (4) for all instructions.
* Single-byte instructions.
* Operations are reg->reg, reg->ram, ram->reg, alu->reg.
* Specific registers can be combined and used as memory addresses.
* Load instructions have 4 bits of immediate data.

There's an assembler which also provides some simple macros, and an extremely simple "compiler".

It would be an interesting exercise to implement some basic optimizations for the compiler, e.g. taking advantage of the number of registers to avoid memory reads/writes on every statement.
