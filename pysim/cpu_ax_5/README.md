This is an extension of cpu_a_6 to add an index register, used by `add`, `nor` and `sta` to modify the memory address. It also adds a 'jnz' conditional jump. The index register can be accessed via the `norx`, `addx` and `stx` instructions. The assembler also provides the same set of macro instructions as for the accumulator.

Having an index register allows working with arrays without needing self-modifying code.

Note that the extra four instructions cost a 1 bit of address-width, which leaves only 32 bytes of accessible RAM... This isn't a very useful CPU! See cpu_ax_13 which adds two-byte instructions, allowing for a 12-bit address space, as well as a banked memory controller.
