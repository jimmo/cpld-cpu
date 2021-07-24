import sys
from sim import (
    Component,
    Signal,
    NotifySignal,
    Net,
    Register,
    SplitRegister,
    BusConnect,
    Clock,
    Ram,
    Rom,
    Power,
    MemDisplay,
)
from .asm import Assembler

# Extends cpu_a_6 to add an index register.

# Built-in ops
# nor addr  --> A = not (A | *(addr + X))  (+CZ)
# add addr  --> A = A + *(addr + X)        (+CZ)
# sta       --> *(addr + X) = A            ()
# norx addr  --> X = not (X | *addr)       (+CZ)
# addx addr  --> A = A + *addr             (+CZ)
# stx       --> *(addr + X) = A            ()
# jcc addr  --> PC = addr                  (-CZ)
# jnz addr  --> PC = addr                  (-CZ)

# Reserved data in RAM
# zero      --> 0x00
# one       --> 0x01
# allone    --> 0xff
# _tmp1     --> 0x..
# _tmp2     --> 0x..


class Decoder(Component):
    def __init__(self):
        super().__init__("decoder")
        self.clk = NotifySignal(self, "clk", 1)
        self.addr = Signal(self, "addr", 5)
        self.data = Signal(self, "data", 8)
        self.we = Signal(self, "we", 1)
        self.oe = Signal(self, "oe", 1)
        self.acc = 0
        self.x = 0
        self.adreg = 0
        self.pc = 0
        self.states = 0

    def reset(self):
        self.addr <<= 0
        self.data <<= None
        self.oe <<= 1
        self.we <<= 0

    def update(self, signal):
        if self.clk.had_edge(0, 1):
            if self.states == 0b0000:
                self.pc = self.adreg + 1
                self.adreg = self.data.value()
            else:
                self.adreg = self.pc

                # ALU / Data Path
                if self.states == 0b0110:
                    # print('  add a {} + {}'.format(self.acc, self.data.value()))
                    self.acc = ((self.acc & 0xFF) + self.data.value()) & 0x1FF
                    # print('    = {}'.format(self.acc))
                elif self.states == 0b0111:
                    # print('  nor a {} + {}'.format(self.acc, self.data.value()))
                    carry = self.acc & 0b100000000
                    value = self.acc & 0xFF
                    nor = (~(value | self.data.value())) & 0xFF
                    self.acc = carry | nor
                    # print('    = {}'.format(self.acc))
                elif self.states == 0b0010:
                    # print('  add x {} + {}'.format(self.x, self.data.value()))
                    self.x = ((self.x & 0xFF) + self.data.value()) & 0x1FF
                elif self.states == 0b0011:
                    # print('  nor x {} + {}'.format(self.x, self.data.value()))
                    carry = self.x & 0b100000000
                    value = self.x & 0xFF
                    nor = (~(value | self.data.value())) & 0xFF
                    self.x = carry | nor
                elif self.states == 0b1101:
                    # Clear carry
                    # print('  j not taken')
                    self.acc = self.acc & 0xFF
                elif self.states == 0b0101:
                    # print('  sta')
                    pass
                elif self.states == 0b0001:
                    # print('  stx')
                    pass
                else:
                    print("  unknown state")

            # State machine
            if self.states != 0b0000:
                self.states = 0b0000
            elif (self.data.value() & 0b01100000) == 0b01100000:
                # print('  maybe jump {} {}'.format(self.acc >> 8, self.acc))
                if not (self.data.value() & 0b10000000) and (self.acc & 0b100000000):
                    # print('  jcc not taken')
                    self.states = 0b1101
                elif (self.data.value() & 0b10000000) and (self.acc & 0xFF) == 0:
                    # print('  jnz not taken')
                    self.states = 0b1101
                else:
                    # print('  branch taken')
                    self.states = 0b0000
            else:
                # print('  going to state for {:03b}'.format(self.data.value() >> 5))
                self.states = ~((self.data.value() >> 5) & 0b111) & 0b111
                if (
                    not (self.data.value() >> 7)
                    and (self.data.value() & 0b01100000) != 0b01100000
                ):
                    # print('offset by x', self.x)
                    self.adreg += self.x

        clk = self.clk.value()
        self.addr <<= self.adreg & 0x1F
        if self.states == 0b0101:
            self.data <<= self.acc & 0xFF
        elif self.states == 0b0001:
            self.data <<= self.x & 0xFF
        else:
            self.data <<= None
        self.oe <<= (
            0
            if (
                clk == 1
                or self.states
                in (
                    0b0001,
                    0b0101,
                    0b1101,
                )
            )
            else 1
        )
        self.we <<= (
            0
            if (
                clk == 1
                or self.states
                not in (
                    0b0001,
                    0b0101,
                )
            )
            else 1
        )


def main():
    power = Power()

    dec = Decoder()

    ram = Ram(addr_width=5)
    out = MemDisplay(addr_width=5, data_addr=2 ** 5 - 5, trigger_addr=2 ** 5 - 4)
    clk = Clock(1)

    dec.clk += clk.clk
    ram.addr += dec.addr + out.addr
    ram.data += dec.data + out.data
    ram.oe += dec.oe
    ram.we += dec.we + out.we

    print("Loading RAM...")

    n = 0
    with Assembler(ram.ram, 0) as asm:
        if not asm.parse(sys.argv[1]):
            return
        asm.hlt()

    ram.stdout()

    for c in (power, dec, ram, clk):
        c.info()
        c.reset()

    last_pc = None
    cycles = 0
    hlt = 0

    try:
        while True:
            clk.tick()

            cycles += 1

            if dec.pc == last_pc:
                hlt += 1
            else:
                hlt = 0
            last_pc = dec.pc
            if hlt > 4:
                break
    except KeyboardInterrupt:
        pass

    print(f"Ran for {cycles} cycles and {Net.net_updates} net updates.")

    ram.stdout()


if __name__ == "__main__":
    main()
