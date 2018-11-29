This is an extension of tinycpu to add an index register, used by `add`, `nor` and `sta`, as well as a 'jnz' conditional jump. The index register can be accessed via the `norx`, `addx` and `stx` instructions, as well as equivalent macro instructions for the accumulator.

Having an index register allows working with arrays without needing self-modifying code.

Note that the extra four instructions cost a 1 bit of address-width, which leaves only 32 bytes of accessible RAM... see index12cpu which adds two-byte instructions, allowing for a 12-bit address space, as well as a banked memory controller.
