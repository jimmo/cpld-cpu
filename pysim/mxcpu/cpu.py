import sys
from sim import Component, Signal, NotifySignal, Net, Register, SplitRegister, BusConnect, Clock, Ram, Rom, Power, MemDisplay
from indexcpu.asm import Assembler

# Implements https://github.com/cpldcpu/MCPU

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

# Derived ops
# clr       --> nor allone
# lda addr  --> clr, add addr
# not       --> nor zero
# sub addr  --> not, add addr, not
# clrx       --> norx allone
# ldx addr  --> clrx, addx addr
# notx       --> norx zero
# subx addr  --> notx, addx addr, notx
# jmp dest  --> jcc dest, jcc dest
# jcs dest  --> jcc *+2, jcc dest
# jz dest  --> jnz *+2, jnz dest

# More derived ops
# shl addr  --> lda addr, add addr

# More logic ops: https://en.wikipedia.org/wiki/NOR_logic
# or addr   --> nor addr, not
# and addr  --> not, sta _tmp1, lda addr, not, nor _tmp1
# nand addr --> and addr, not
# xnor addr --> sta _tmp1, nor addr, sta _tmp2, nor _tmp1, sta _tmp1, lda _tmp2, nor addr, nor _tmp1
# xor addr  --> sta _tmp1, not, nor addr, sta _tmp2, lda addr, not, nor _tmp1, nor _tmp2

# xxxd dddd  (5-bit addressing --> 64 bytes RAM)

# Clock | States | ie | oe

# Fetch
#  0    |  000   | 0  | 1
#  /
#  1    |  000   | 0  | 0

# Store Acc
#  0    |  001   | 1  | 0
#  /
#  1    |  001   | 0  | 0

# Add
#  0    |  010   | 0  | 1
#  /
#  1    |  010   | 0  | 0

# Nor
#  0    |  011   | 0  | 1
#  /
#  1    |  011   | 0  | 0

# Branch not taken
#  0    |  101   | 0  | 0
#  1    |  101   | 0  | 0

class Decoder(Component):
  def __init__(self):
    super().__init__('decoder')
    self.clk = NotifySignal(self, 'clk', 1)
    self.addr = Signal(self, 'addr', 5)
    self.data = Signal(self, 'data', 8)
    self.ie = Signal(self, 'ie', 1)
    self.oe = Signal(self, 'oe', 1)
    self.acc = 0
    self.x = 0
    self.adreg = 0
    self.pc = 0
    self.states = 0

  def reset(self):
    self.addr <<= 0
    self.data <<= None
    self.oe <<= 1
    self.ie <<= 0

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
          self.acc = ((self.acc & 0xff) + self.data.value()) & 0x1ff
          # print('    = {}'.format(self.acc))
        elif self.states == 0b0111:
          # print('  nor a {} + {}'.format(self.acc, self.data.value()))
          carry = self.acc & 0b100000000
          value = self.acc & 0xff
          nor = (~(value | self.data.value())) & 0xff
          self.acc = carry | nor
          # print('    = {}'.format(self.acc))
        elif self.states == 0b0010:
          # print('  add x {} + {}'.format(self.x, self.data.value()))
          self.x = ((self.x & 0xff) + self.data.value()) & 0x1ff
        elif self.states == 0b0011:
          # print('  nor x {} + {}'.format(self.x, self.data.value()))
          carry = self.x & 0b100000000
          value = self.x & 0xff
          nor = (~(value | self.data.value())) & 0xff
          self.x = carry | nor
        elif self.states == 0b1101:
          # Clear carry
          #print('  j not taken')
          self.acc = self.acc & 0xff
        elif self.states == 0b0101:
          # print('  sta')
          pass
        elif self.states == 0b0001:
          # print('  stx')
          pass
        else:
          print('  unknown state')

      # State machine
      if self.states != 0b0000:
        self.states = 0b0000
      elif (self.data.value() & 0b01100000) == 0b01100000:
        # print('  maybe jump {} {}'.format(self.acc >> 8, self.acc))
        if not (self.data.value() & 0b10000000) and (self.acc & 0b100000000):
          # print('  jcc not taken')
          self.states = 0b1101
        elif (self.data.value() & 0b10000000) and (self.acc & 0xff) == 0:
          # print('  jnz not taken')
          self.states = 0b1101
        else:
          # print('  branch taken')
          self.states = 0b0000
      else:
        #print('  going to state for {:03b}'.format(self.data.value() >> 5))
        self.states = ~((self.data.value() >> 5) & 0b111) & 0b111
        if not (self.data.value() >> 7) and (self.data.value() & 0b01100000) != 0b01100000:
          #print('offset by x', self.x)
          self.adreg += self.x

    clk = self.clk.value()
    self.addr <<= self.adreg & 0x1f
    if self.states == 0b0101:
      self.data <<= self.acc & 0xff
    elif self.states == 0b0001:
      self.data <<= self.x & 0xff
    else:
      self.data <<= None
    self.oe <<= 0 if (clk == 1 or self.states in (0b0001, 0b0101, 0b1101,)) else 1
    self.ie <<= 0 if (clk == 1 or self.states not in (0b0001, 0b0101,)) else 1



def main():
  power = Power()

  dec = Decoder()
  
  ram = Ram(addr_width=5)
  out = MemDisplay(addr_width=5, data_addr=2**5-5, trigger_addr=2**5-4)
  clk = Clock(1)

  dec.clk += clk.clk
  ram.addr += dec.addr + out.addr
  ram.data += dec.data + out.data
  ram.oe += dec.oe
  ram.ie += dec.ie + out.ie

  print('Loading RAM...')

  n = 0
  with Assembler(ram.ram, 0) as asm:
    if not asm.parse(sys.argv[1]):
      return
    asm.hlt()

  ram.stdout()

  for c in (
      power,
      dec,
      ram,
      clk):
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

  print(f'Ran for {cycles} cycles and {Net.net_updates} net updates.')

  ram.stdout()

if __name__ == '__main__':
  main()
