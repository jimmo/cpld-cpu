import sys
from sim import (
    Component,
    Signal,
    NotifySignal,
    Net,
    Register,
    IORegister,
    IncRegister,
    Clock,
    Ram,
    Rom,
    Power,
    MemDisplay,
)
from .asm import Assembler


class ALU(Component):
    def __init__(self):
        super().__init__("alu")
        self.a = Signal(self, "a", 9)
        self.b = Signal(self, "b", 8)
        self.out = Signal(self, "out", 9)
        self.fn = Signal(self, "fn", 1)
        self.oe = NotifySignal(self, "oe", 1)
        self.we = NotifySignal(self, "we", 1)
        self.v = 0

    def update(self, signal):
        if self.we.had_edge(0, 1):
            if self.fn.value() == 0:
                # nor
                # print('alu nor {} {}'.format(self.a.value(), self.b.value()))
                carry = self.a.value() & 0b100000000
                value = self.a.value() & 0xFF
                self.v = carry | ((~(value | self.b.value())) & 0xFF)
            else:
                # add
                # print('alu add {} {}'.format(self.a.value(), self.b.value()))
                self.v = ((self.a.value() & 0xFF) + self.b.value()) & 0x1FF

            # print(' --> {}'.format(self.v))

        if self.oe.value() == 1:
            self.out <<= self.v
        else:
            self.out <<= None


class AccumulatorRegister(IORegister):
    def __init__(self):
        super().__init__("accumulator", width=9)
        self.z = Signal(self, "z", 1)
        self.cc = NotifySignal(self, "cc", 1)

    def update(self, signal):
        super().update(signal)
        self.z <<= 1 if self.v == 0 else 0
        if self.cc.had_edge(0, 1):
            self.v = self.v & 0xFF


class Decoder(Component):
    def __init__(self):
        super().__init__("decoder")

        self.clk = NotifySignal(self, "clk", 1)

        self.ram_oe = Signal(self, "ram_oe", 1)
        self.ram_we = Signal(self, "ram_oe", 1)
        self.ar_oe = Signal(self, "ar_oe", 1)
        self.ar_we = Signal(self, "ar_we", 1)
        self.ir_oe = Signal(self, "ir_oe", 1)
        self.ir_we = Signal(self, "ir_we", 1)
        self.pc_we = Signal(self, "pc_we", 1)
        self.pc_oe = Signal(self, "pc_oe", 1)
        self.pc_inc = Signal(self, "pc_inc", 1)
        self.a_oe = Signal(self, "a_oe", 1)
        self.a_we = Signal(self, "a_we", 1)
        self.a_cc = Signal(self, "a_cc", 1)
        self.alu_oe = Signal(self, "alu_oe", 1)
        self.alu_we = Signal(self, "alu_we", 1)

        self.carry = Signal(self, "carry", 1)
        self.z = Signal(self, "z", 1)
        self.fn = Signal(self, "fn", 1)

        self.instr = Signal(self, "instr", 2)

        self.state = 0

    def reset(self):
        self.ram_oe <<= 0
        self.ram_we <<= 0
        self.ar_oe <<= 0
        self.ar_we <<= 0
        self.ir_oe <<= 0
        self.ir_we <<= 0
        self.pc_we <<= 0
        self.pc_oe <<= 0
        self.pc_inc <<= 0
        self.a_oe <<= 0
        self.a_we <<= 0
        self.a_cc <<= 0
        self.alu_oe <<= 0
        self.alu_we <<= 0

        self.fn <<= 0

    def update(self, signal):
        if self.clk.had_edge(0, 1):
            self.state = (self.state + 1) % 8
            # print('state: {}: instr: {:02b}'.format(self.state, self.instr.value()))

        self.ram_oe <<= self.state <= 3 or (
            self.instr.value()
            in (
                0b00,
                0b01,
            )
            and self.state <= 5
        )
        # not (self.instr.value() == 0b10 and self.state in (5, 6,))

        # self.pc_oe <<= 0
        # self.ir_oe <<= 0
        # self.ar_oe <<= 0
        # self.a_oe <<= 0

        self.ar_oe <<= self.state > 3
        self.ir_oe <<= self.state > 3
        self.pc_oe <<= self.state <= 3
        self.ir_we <<= self.state == 1
        self.pc_inc <<= self.state in (
            2,
            4,
        )
        self.ar_we <<= self.state == 3

        # alu
        self.alu_we <<= (
            self.instr.value()
            in (
                0b00,
                0b01,
            )
            and self.state == 5
        )
        self.alu_oe <<= self.instr.value() in (0b00, 0b01,) and self.state in (
            5,
            6,
        )
        self.a_we <<= (
            self.instr.value()
            in (
                0b00,
                0b01,
            )
            and self.state == 6
        )
        self.fn <<= self.instr.value() & 1

        # sta
        self.a_oe <<= self.instr.value() == 0b10 and self.state in (
            5,
            6,
        )
        self.ram_we <<= self.instr.value() == 0b10 and self.state == 6

        # jcc c=0
        self.pc_we <<= (
            self.instr.value() == 0b11 and self.carry.value() == 0 and self.state == 5
        )
        # jcc c=1
        self.a_cc <<= (
            self.instr.value() == 0b11 and self.carry.value() != 0 and self.state == 5
        )


def main():
    dec = Decoder()

    ram = Ram(addr_width=14)
    out = MemDisplay(addr_width=14, data_addr=2 ** 14 - 5, trigger_addr=2 ** 14 - 4)
    clk = Clock(1)

    acc = AccumulatorRegister()
    ir = IORegister("ir")
    ar = IORegister("ar")
    pcl = IncRegister("pcl", width=8)
    pch = IncRegister("pch", width=6)
    alu = ALU()

    dec.clk += clk.clk

    ram.addr[0:8] += ar.out + pcl.out + out.addr[0:8]
    ram.addr[8:14] += ir.out[0:6] + pch.out + out.addr[8:14]
    pcl.oe += pch.oe + dec.pc_oe
    ir.oe += dec.ir_oe
    ar.oe += dec.ar_oe

    ram.data += out.data + ir.inp + ar.inp + alu.b + acc.out[0:8]
    acc.inp += alu.out

    ar.we += dec.ar_we
    ir.we += dec.ir_we
    pcl.we += pch.we + dec.pc_we
    pcl.inc += dec.pc_inc
    pch.inc += pcl.carry

    dec.instr += ir.state[6:8]
    pcl.inp += ar.state
    pch.inp += ir.state[0:6]

    acc.cc += dec.a_cc

    ram.oe += dec.ram_oe
    ram.we += dec.ram_we + out.we

    acc.oe += dec.a_oe
    acc.we += dec.a_we

    alu.oe += dec.alu_oe
    alu.we += dec.alu_we

    dec.carry += acc.state[8]
    dec.z += acc.z

    alu.a += acc.state
    alu.fn += dec.fn

    pcl.state.nc()
    pch.state.nc()
    pch.carry.nc()
    ir.out[6:8].nc()
    acc.out[8].nc()

    print("Loading RAM...")

    n = 0
    with Assembler(ram.ram, 0) as asm:
        if not asm.parse(sys.argv[1]):
            return
        asm.hlt()

    ram.stdout()

    for c in (
        dec,
        ram,
        out,
        clk,
        acc,
        ar,
        ir,
        pcl,
        pch,
        alu,
    ):
        c.info()
        c.reset()

    last_pc = None
    cycles = 0
    hlt = 0

    try:
        while True:
            clk.tick()

            cycles += 1

            if dec.state == 0:
                if pcl.value() == last_pc:
                    hlt += 1
                else:
                    hlt = 0
                last_pc = pcl.value()
                if hlt > 1:
                    break
    except KeyboardInterrupt:
        pass

    print(f"Ran for {cycles} cycles and {Net.net_updates} net updates.")

    ram.stdout()


if __name__ == "__main__":
    main()
