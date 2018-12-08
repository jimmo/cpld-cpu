This adds both the index register and two-byte instructions. Each instruction is a 3-bit op, and 13-bit address.

The memory controller also implements paged addressing, with two pages, allowing for 1MiB of addressable RAM.
There are two memory-mapped registers which set the physical address for that page (in 4k intervals).

So each address is a 1-bit page number (_n)), and a 12-bit offset (_addr_). The physical address will be the PR[_n_] * 4k + _addr_.

Two basic memory-mapped perhipherals are available: LED output and RNG.
