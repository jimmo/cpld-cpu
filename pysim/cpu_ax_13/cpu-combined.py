import sys
from sim import Component, Signal, NotifySignal, Net, Register, SplitRegister, BusConnect, Clock, Ram, Rom, Power, MemDisplay, PagedRamController
from .asm import Assembler


class Decoder(Component):
  MASK_OP = 0b011
  MASK_REG = 0b100
  OP_NOR = 0b000
  OP_ADD = 0b001
  OP_ST = 0b010
  OP_J = 0b011
  REG_A = 0b000
  REG_X = 0b100
  
  def __init__(self):
    super().__init__('decoder')
    self.clk = NotifySignal(self, 'clk', 1)
    self.addr = Signal(self, 'addr', 13)
    self.data = Signal(self, 'data', 8)
    self.we = Signal(self, 'we', 1)
    self.oe = Signal(self, 'oe', 1)
    self.acc = 0
    self.x = 0
    self.adreg = 0
    self.hi5 = 0
    self.pc = 0
    self.state = 0
    self.op = 0

  def reset(self):
    self.addr <<= 0
    self.data <<= None
    self.oe <<= 1
    self.we <<= 0

  def update(self, signal):
    if self.clk.had_edge(0, 1):
      # print('clock {}'.format(self.state))
      if self.state == 0:
        self.pc = self.adreg + 2
        self.adreg = self.adreg + 1
        self.op = (self.data.value() >> 5) & 0b111
        self.hi5 = self.data.value() & 0x1f
      elif self.state == 1:
        self.adreg = (self.hi5 << 8) | self.data.value()
      elif self.state == 2:
        self.adreg = self.pc

        # ALU / Data Path
        if self.op == Decoder.REG_A | Decoder.OP_ADD:
          # print('  add a {} + {}'.format(self.acc, self.data.value()))
          self.acc = ((self.acc & 0xff) + self.data.value()) & 0x1ff
          # print('    = {}'.format(self.acc))
        elif self.op == Decoder.REG_A | Decoder.OP_NOR:
          # print('  nor a {} + {}'.format(self.acc, self.data.value()))
          carry = self.acc & 0b100000000
          value = self.acc & 0xff
          nor = (~(value | self.data.value())) & 0xff
          self.acc = carry | nor
          # print('    = {}'.format(self.acc))
        elif self.op == Decoder.REG_X | Decoder.OP_ADD:
          # print('  add x {} + {}'.format(self.x, self.data.value()))
          self.x = ((self.x & 0xff) + self.data.value()) & 0x1ff
        elif self.op == Decoder.REG_X | Decoder.OP_NOR:
          # print('  nor x {} + {}'.format(self.x, self.data.value()))
          carry = self.x & 0b100000000
          value = self.x & 0xff
          nor = (~(value | self.data.value())) & 0xff
          self.x = carry | nor
        elif (self.op & Decoder.MASK_OP) == Decoder.OP_J:
          # Clear carry on all non-taken jumps.
          # print('  j not taken')
          self.acc = self.acc & 0xff
        elif (self.op & Decoder.MASK_OP) == Decoder.OP_ST:
          # print('  sta / stx')
          pass
        else:
          print('  unknown op')
      else:
        print('unknown state')

      # State machine
      if self.state == 0:
        # print('get next byte')
        self.state = 1
      elif self.state == 2:
        self.state = 0
      elif self.state == 1:
        if (self.op & Decoder.MASK_OP) == Decoder.OP_J:
          # print('  maybe jump {} {}'.format(self.acc >> 8, self.acc))
          if self.op & Decoder.MASK_REG == Decoder.REG_A and (self.acc & 0b100000000):
            # print('  jcc not taken')
            self.state = 2
          elif self.op & Decoder.MASK_REG == Decoder.REG_X and (self.acc & 0xff) == 0:
            # print('  jnz not taken')
            self.state = 2
          else:
            # print('  branch taken')
            self.state = 0
        else:
          self.state = 2
          # print('  going to state={} op={:03b}'.format(self.state, self.op))
          if self.op & Decoder.MASK_REG == 0:
            # print('offset by x', self.x)
            self.adreg += self.x
      else:
        print('unknown state')

    clk = self.clk.value()
    # print('addr: {:04x}'.format(self.adreg & 0x1fff))
    self.addr <<= self.adreg & 0x1fff

    if self.state == 2 and self.op == Decoder.REG_A | Decoder.OP_ST:
      self.data <<= self.acc & 0xff
    elif self.state == 2 and self.op == Decoder.REG_X | Decoder.OP_ST:
      self.data <<= self.x & 0xff
    else:
      self.data <<= None
      
    if clk == 1:
      self.oe <<= 0
      self.we <<= 0
    else:
      if self.state == 2 and (self.op & Decoder.MASK_OP) == Decoder.OP_ST:
        self.oe <<= 0
      else:
        self.oe <<= 1

      if self.state == 2 and (self.op & Decoder.MASK_OP) == Decoder.OP_ST:
        self.we <<= 1
      else:
        self.we <<= 0


def main():
  dec = Decoder()
  
  ram = Ram(addr_width=20)
  paged_ram = PagedRamController(addr_width=13, num_pages=2, reg_base_addr=2**12-7)
  out = MemDisplay(addr_width=12, data_addr=2**12-5, trigger_addr=2**12-4)
  clk = Clock(1)

  dec.clk += clk.clk

  paged_ram.in_addr[0:12] += ram.addr[0:12] + dec.addr[0:12] + out.addr
  paged_ram.in_addr[12] += dec.addr[12]
  ram.addr[12:20] += paged_ram.out_addr
  
  ram.data += dec.data + out.data + paged_ram.data
  
  ram.oe += dec.oe
  ram.we += dec.we + out.we + paged_ram.we

  print('Loading RAM...')

  n = 0
  with Assembler(ram.ram, 0) as asm:
    if not asm.parse(sys.argv[1]):
      return

  ram.stdout()

  for c in (
      dec,
      ram,
      paged_ram,
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
      if hlt > 10:# or cycles > 60:
        break
  except KeyboardInterrupt:
    pass

  print(f'Ran for {cycles} cycles and {Net.net_updates} net updates.')

  ram.stdout()

if __name__ == '__main__':
  main()
