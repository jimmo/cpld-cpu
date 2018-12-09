import sys
from sim import Component, Signal, NotifySignal, IORegister, IncRegister, Clock, Ram, Net, MemDisplay, Multiplexer, PagedRamController, debug, trace, warn, RNG
from .asm import Assembler


class ALU(Component):
  def __init__(self):
    super().__init__('alu')
    self.a = Signal(self, 'a', 9)
    self.b = Signal(self, 'b', 8)
    self.out = Signal(self, 'out', 9)
    self.fn = Signal(self, 'fn', 1)
    self.oe = NotifySignal(self, 'oe', 1)
    self.we = NotifySignal(self, 'we', 1)
    self.v = 0

  def update(self, signal):
    if self.we.had_edge(0, 1):
      if self.fn.value() == 0:
        # nor
        trace('alu nor {} {}'.format(self.a.value(), self.b.value()), end='')
        carry = self.a.value() & 0b100000000
        value = self.a.value() & 0xff
        self.v = carry | ((~(value | self.b.value())) & 0xff)
      else:
        # add
        trace('alu add {} {}'.format(self.a.value(), self.b.value()), end='')
        self.v = ((self.a.value() & 0xff) + self.b.value()) & 0x1ff

      trace(' --> {}'.format(self.v))

    if self.oe.value() == 1:
      self.out <<= self.v
    else:
      self.out <<= None


class AccumulatorRegister(IORegister):
  def __init__(self):
    super().__init__('accumulator', width=9)
    self.z = Signal(self, 'z', 1)
    self.cc = NotifySignal(self, 'cc', 1)

  def update(self, signal):
    super().update(signal)
    self.z <<= 1 if self.v == 0 else 0
    if self.cc.had_edge(0, 1):
      self.v = self.v & 0xff

    
class Decoder(Component):
  def __init__(self):
    super().__init__('decoder')
    
    self.clk = NotifySignal(self, 'clk', 1)
    
    self.ram_oe = Signal(self, 'ram_oe', 1)
    self.ram_we = Signal(self, 'ram_oe', 1)
    self.ar_oe = Signal(self, 'ar_oe', 1)
    self.ar_we = Signal(self, 'ar_we', 1)
    self.ir_oe = Signal(self, 'ir_oe', 1)
    self.ir_we = Signal(self, 'ir_we', 1)
    self.pc_we = Signal(self, 'pc_we', 1)
    self.pc_oe = Signal(self, 'pc_oe', 1)
    self.pc_inc = Signal(self, 'pc_inc', 1)
    self.a_oe = Signal(self, 'a_oe', 1)
    self.a_we = Signal(self, 'a_we', 1)
    self.a_cc = Signal(self, 'a_cc', 1)
    self.x_oe = Signal(self, 'a_oe', 1)
    self.x_we = Signal(self, 'a_we', 1)
    self.alu_oe = Signal(self, 'alu_oe', 1)
    self.alu_we = Signal(self, 'alu_we', 1)
    self.idx_en = Signal(self, 'idx_en', 1)
    
    self.carry = Signal(self, 'carry', 1)
    self.z = Signal(self, 'z', 1)

    self.instr = Signal(self, 'instr', 3)

    self.state = 0
    self.last_clk = None

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
    self.x_oe <<= 0
    self.x_we <<= 0
    self.alu_oe <<= 1
    self.alu_we <<= 0
    self.idx_en <<= 0

  def update(self, signal):
    if self.clk.value() != self.last_clk:
      self.state = (self.state + 1) % 8
      self.last_clk = self.clk.value()
    else:
      return
      #print('state: {}: instr: {:02b}'.format(self.state, self.instr.value()))

    self.ram_oe <<= self.state <= 3 or (self.instr.value() in (0b000, 0b001, 0b100, 0b101) and self.state <= 5)

    self.ar_oe <<= self.state > 3
    self.ir_oe <<= self.state > 3
    self.pc_oe <<= self.state <= 3
    self.ir_we <<= self.state == 1
    self.pc_inc <<= self.state in (2, 4,)
    self.ar_we <<= self.state == 3

    # alu
    self.alu_we <<= self.instr.value() in (0b000, 0b001, 0b100, 0b101) and self.state == 5
    #self.alu_oe <<= self.instr.value() in (0b000, 0b001, 0b100, 0b101) and self.state in (5, 6,)
    self.a_we <<= self.instr.value() in (0b000, 0b001,) and self.state == 6
    self.x_we <<= self.instr.value() in (0b100, 0b101) and self.state == 6

    # sta/stx
    self.a_oe <<= self.instr.value() == 0b010 and self.state in (5, 6,)
    self.x_oe <<= self.instr.value() == 0b110 and self.state in (5, 6,)
    self.ram_we <<= self.instr.value() in (0b010, 0b110,) and self.state == 6

    # Indexing for alu(a), sta
    self.idx_en <<= self.instr.value() in (0b000, 0b001, 0b010) and self.state > 3

    # jcc c=0 / jnz z=0
    self.pc_we <<= ((self.instr.value() == 0b011 and self.carry.value() == 0) or (self.instr.value() == 0b111 and self.z.value() == 0)) and self.state == 5
    # jcc c=1 / jnz z=1
    self.a_cc <<= ((self.instr.value() == 0b011 and self.carry.value() != 0) or (self.instr.value() == 0b111 and self.z.value() != 0)) and self.state == 5


class RamIndex(Component):
  def __init__(self):
    super().__init__('ram_index')
    self.addr = NotifySignal(self, 'addr', 12)
    self.x = NotifySignal(self, 'x', 8)
    self.out = Signal(self, 'out', 12)
    self.en = NotifySignal(self, 'en', 1)

  def update(self, signal):
    if self.en.value():
      #print('offset by {}'.format(self.x.value()))
      self.out <<= self.addr.value() + self.x.value()
    else:
      self.out <<= self.addr.value()
    

def main():
  dec = Decoder()
  
  clk = Clock(1)
  
  ram = Ram(addr_width=20)
  paged_ram = PagedRamController(addr_width=13, num_pages=2, reg_base_addr=2**12-7)
  ram_index = RamIndex()

  out = MemDisplay(addr_width=20, base_addr=2**12 - 5)
  rng = RNG(addr_width=20, base_addr=2**12 - 6)

  acc = AccumulatorRegister()
  x = IORegister('x')
  ir = IORegister('ir')
  ar = IORegister('ar')
  pcl = IncRegister('pcl', width=8)
  pch = IncRegister('pch', width=5)
  alu = ALU()

  ax_alu = Multiplexer('ax_alu')

  dec.clk += clk.clk

  ram_index.addr[0:8] += ar.out + pcl.out
  ram_index.addr[8:12] += ir.out[0:4] + pch.out[0:4]
  ram_index.x += x.state
  ram_index.en += dec.idx_en
  paged_ram.in_addr[0:12] += ram_index.out
  paged_ram.in_addr[12] += ir.out[4] + pch.out[4]

  ram.addr += out.addr + rng.addr
  ram.addr[0:12] += paged_ram.in_addr[0:12]
  ram.addr[12:20] += paged_ram.out_addr
  
  pcl.oe += pch.oe + dec.pc_oe
  ir.oe += dec.ir_oe
  ar.oe += dec.ar_oe
  
  ram.data += out.data + rng.data + ir.inp + ar.inp + alu.b + acc.out[0:8] + x.out + paged_ram.data
  alu.out += acc.inp
  alu.out[0:8] += x.inp

  ar.we += dec.ar_we
  ir.we += dec.ir_we
  pcl.we += pch.we + dec.pc_we
  pcl.inc += dec.pc_inc
  pch.inc += pcl.carry

  dec.instr += ir.state[5:8]
  pcl.inp += ar.state
  pch.inp += ir.state[0:5]

  acc.cc += dec.a_cc

  out.oe += dec.ram_oe
  rng.oe += out.oe_out
  ram.oe += rng.oe_out

  out.we += dec.ram_we + paged_ram.we
  rng.we += out.we_out
  ram.we += rng.we_out

  acc.oe += dec.a_oe
  acc.we += dec.a_we
  x.oe += dec.x_oe
  x.we += dec.x_we

  alu.oe += dec.alu_oe
  alu.we += dec.alu_we

  dec.carry += acc.state[8]
  dec.z += acc.z

  ax_alu.a += acc.state[0:8]
  ax_alu.b += x.state
  ax_alu.sel += ir.state[7]
  alu.a[0:8] += ax_alu.out
  alu.a[8] += acc.state[8]
  alu.fn += ir.state[5]

  pcl.state.nc()
  pch.state.nc()
  pch.carry.nc()
  ir.out[5:8].nc()
  acc.out[8].nc()

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
      ram_index,
      out,
      rng,
      clk,
      acc,
      x,
      ar,
      ir,
      pcl,
      pch,
      alu,
      ax_alu,
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

  print(f'Ran for {cycles} cycles and {Net.net_updates} net updates.')

  ram.stdout()

if __name__ == '__main__':
  main()
