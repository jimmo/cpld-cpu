import sys
from sim import Component, Signal, NotifySignal, Net, Register, SplitRegister, BusConnect, Clock, Ram, Rom, Power
from tinycpu.asm import Assembler

# Implements https://github.com/cpldcpu/MCPU

# Built-in ops
# nor addr  --> A = not (A | *addr)  (+C)
# add addr  --> A = A + *addr        (+C)
# sta       --> *addr = A            ()
# jcc addr  --> PC = addr            (-C)

# Reserved data in RAM
# zero      --> 0x00
# one       --> 0x01
# allone    --> 0xff

# Derived ops
# clr       --> nor allone
# lda addr  --> clr, add addr
# not       --> nor zero
# jmp dest  --> jcc dest, jcc dest
# jcs dest  --> jcc *+2, jcc dest
# sub addr  --> not, add addr, add one

# More derived ops
# shl addr  --> lda addr, add addr

# xxdd dddd  (6-bit addressing --> 64 bytes RAM)


class Decoder(Component):
  def __init__(self):
    super().__init__('decoder')
    self.clk = NotifySignal(self, 'clk', 1)
    self.addr = Signal(self, 'addr', 6)
    self.data = Signal(self, 'data', 8)
    self.ie = Signal(self, 'ie', 1)
    self.oe = Signal(self, 'oe', 1)
    self.acc = 0
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
      if self.states == 0b000:
        self.pc = self.adreg + 1
        self.adreg = self.data.value()
      else:
        self.adreg = self.pc

      # ALU / Data Path
      if self.states == 0b010:
        self.acc = ((self.acc & 0xff) + self.data.value()) & 0x1ff
      elif self.states == 0b011:
        self.acc = ~((self.acc & 0xff) | self.data.value()) & 0xff
      elif self.states == 0b101:
        # Clear carry
        self.acc = self.acc & 0xff

      # State machine
      if self.states != 0b000:
        self.states = 0b000
      elif (self.data.value() & 0b11000000) == 0b11000000 and self.acc & 0b100000000:
        self.states = 0b101
      else:
        self.states = ~((self.data.value() >> 6) & 0b11) & 0b11

    clk = self.clk.value()
    self.addr <<= self.adreg & 0x3f
    self.data <<= None if self.states != 0b001 else self.acc & 0xff
    self.oe <<= 0 if (clk == 1 or self.states == 0b001 or self.states == 0b101) else 1
    self.ie <<= 0 if (clk == 1 or self.states != 0b001) else 1

    
class MemDisplay(Component):
  def __init__(self, addr_width=16, data_width=8, data_addr=0, trigger_addr=0):
    super().__init__('mem display')
    self.data_addr = data_addr
    self.trigger_addr = trigger_addr
    self.v = 0
    self.addr = NotifySignal(self, 'addr', addr_width)
    self.data = Signal(self, 'data', data_width)
    self.ie = NotifySignal(self, 'ie', 1)

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      if self.addr.value() == self.data_addr:
        self.v = self.data.value()
      if self.addr.value() == self.trigger_addr and self.data.value() == 1:
        print(self.v)


def main():
  power = Power()

  dec = Decoder()
  
  ram = Ram(addr_width=6)
  out = MemDisplay(addr_width=6, data_addr=59, trigger_addr=60)
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

  print('RAM:')
  for i in range(0, 64, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in ram.ram[i:i+16])))

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

      # print('RAM:')
      # for i in range(0, 64, 16):
      #   print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in ram.ram[i:i+16])))

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

  print('RAM:')
  for i in range(0, 64, 16):
    print('{:04x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in ram.ram[i:i+16])))

if __name__ == '__main__':
  main()
