This is an extension of mxcpu to support two-byte instructions and paged addressing, allowing for 1MiB of addressable RAM.

Each instruction is a 3-bit op, and 13-bit address.

The 13-bit address space is divided into two pages:
0 -> 4095:   Maps directly to RAM. Contains all memory-mapped IO, including page register.
4096->8191:  Maps to (addr-4096) * Page Register.

As all eight instructions require a memory address, they are all two-bytes long.
