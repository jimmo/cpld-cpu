import sys
from sim import Component, Signal, Register, BusConnect, Clock, Ram, Rom, Power

# 0ddnxxxx  load imm dd=A,B,C,D n=h/l xxxx=data
# 10sssddd  mov sss to ddd  rrr=A,B,C,D,E,F,G,H
# 110ffffd  ALU ffff for d (A or C)
# 1110?wtt  r/w mem tt=(C:D, E:F, E:F, G:H) read=(B,B,D,D), write=(A,A,C,C)
# 1111rttt  jump r=(E:F, G:H)


class Inst:
  @classmethod
  def load(cls, reg, nibble):
    reg = reg.lower()
    if len(reg) != 2 or reg[0] not in ('a', 'b', 'c', 'd',) or reg[1] not in ('l', 'h',):
      raise ValueError(f'Invalid register for load: {reg}.')
    index = ord(reg[0]) - ord('a')
    return (nibble) | (0b10000 if reg[1] == 'h' else 0) | (index << 5)

  @classmethod
  def mov(dst, src):
    dst = dst.lower()
    src = src.lower()
    if len(dst) != 1:
      raise ValueError(f'Invalid destination register: {dst}')
    if len(src) != 1:
      raise ValueError(f'Invalid source register: {src}')
    return (1<<7) | ((ord(src) - ord('a'))<<3) | (ord(dst) - ord('a'))

  def add(dst):
    dst = dst.lower()
    if dst not in ('a', 'c',):
      raise ValueError(f'Invalid destination register for add: {reg}.')
    return 0


class Logic(Component):
  def __init__(self):
    super().__init__('logic')
    self.a = Signal(self, 'a', 8)
    self.b = Signal(self, 'b', 8)
    self.fn = Signal(self, 'fn', 4)
    self.out = Signal(self, 'out', 8)
    self.flags = Signal(self, 'flags', 4)
    self.oe = Signal(self, 'oe', 1)

  def update(self, signal):
    if self.oe.value():
      a = self.a.value()
      b = self.b.value()
      o = 0
      fn = self.fn.value()
      if fn == 0:
        o = a + b
      elif fn == 1:
        o = a - b
      elif fn == 2:
        o = a > b
      elif fn == 3:
        o = a < b
      elif fn == 4:
        o = a == b
      elif fn == 5:
        o = a & b
      elif fn == 6:
        o = a | b
      elif fn == 7:
        o = a ^ b
      elif fn == 8:
        o = ~a
      elif fn == 9:
        o = a == 0
      elif fn == 10:
        o = a >> 1
      elif fn == 11:
        o = b << 1
      elif fn == 12:
        o = a
      elif fn == 13:
        o = a
      elif fn == 14:
        o = a
      elif fn == 15:
        o = a
      self.out <<= (o % 0x100)
    else:
      self.out <<= None
      self.flags <<= None


class Decoder(Component):
  def __init__(self):
    super().__init__('decoder')
    self.instr = Signal(self, 'instr', 8)
    self.clk = Signal(self, 'clk', 2)
    self.a_ie = Signal(self, 'a_ie', 2)
    self.b_ie = Signal(self, 'b_ie', 2)
    self.c_ie = Signal(self, 'c_ie', 2)
    self.d_ie = Signal(self, 'd_ie', 2)
    self.a_to_b = Signal(self, 'a_to_b', 1)
    self.b_to_a = Signal(self, 'b_to_a', 1)
    self.pc_inc = Signal(self, 'pc_inc', 1)
    self.ir_ie = Signal(self, 'ir_ie', 1)
    self.ir_oe = Signal(self, 'ir_oe', 1)

  def reset(self):
    self.pc_inc <<= 0

  def update(self, signal):
    m1 = self.clk.value() <= 1
    m2 = self.clk.value() == 1
    m3 = self.clk.value() >= 2
    m4 = self.clk.value() == 3
    #print('m1' if m1 else '', 'm2' if m2 else '', 'm3' if m3 else '', 'm4' if m4 else '')

    instr = self.instr.value()

    self.ir_ie <<= m1
    self.pc_inc <<= m4

    b7 = ((instr >> 7) & 1)
    b6 = ((instr >> 6) & 1)
    b5 = ((instr >> 5) & 1)
    b4 = ((instr >> 4) & 1)

    is_imm = not b7
    is_imm_high = ((instr >> 4) & 1)
    is_imm_a = ((instr >> 5) & 3) == 0
    is_imm_b = ((instr >> 5) & 3) == 1
    is_imm_c = ((instr >> 5) & 3) == 2
    is_imm_d = ((instr >> 5) & 3) == 3

    is_mov = b7 and not b6

    is_alu = b7 and b6 and not b5

    is_mem = b7 and b6 and b5 and not b4

    is_jmp = b7 and b6 and b5 and b4

    self.ir_oe <<= (m3 & is_imm)
    self.a_ie <<= ((m4 & is_imm & is_imm_a) << is_imm_high)
    self.b_ie <<= ((m4 & is_imm & is_imm_b) << is_imm_high)
    self.c_ie <<= ((m4 & is_imm & is_imm_c) << is_imm_high)
    self.d_ie <<= ((m4 & is_imm & is_imm_d) << is_imm_high)

    self.a_to_b <<= (m3 & is_imm & (is_imm_b | is_imm_d))


class InstructionRegister(Component):
  def __init__(self):
    super().__init__('ir')
    self.v = 0
    self.data = Signal(self, 'data', 8)
    self.instr = Signal(self, 'instr', 8)
    self.imm = Signal(self, 'imm', 8)
    self.ie = Signal(self, 'ie', 1)
    self.oe = Signal(self, 'oe', 1)

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      #print('reg ir load 0x{:02x}'.format(self.data.value()))
      self.v = self.data.value()
      self.instr <<= self.v
    if self.oe.value():
      imm = (self.v & 0xf)
      self.imm <<= (imm | imm << 4)
    else:
      self.imm <<= None


class ProgramCounter(Component):
  def __init__(self, n):
    super().__init__('pc ' + n)
    self.v = 0
    self.addr = Signal(self, 'addr', 8)
    self.data = Signal(self, 'data', 8)
    self.rst = Signal(self, 'rst', 1)
    self.inc = Signal(self, 'inc', 1)
    self.ie = Signal(self, 'ie', 1)
    self.co = Signal(self, 'co', 1)

  def update(self, signal):
    if self.rst.value() == 1:
      self.v = 0
    elif self.ie.value():
      self.v = self.data.value()
    elif self.inc.had_edge(0, 1):
      if self.v == 0xff:
        self.v = 0
        self.co <<= 1
      else:
        self.v += 1
        self.co <<= 0
    self.addr <<= self.v


# class BranchFlags(Component):
#   def __init__(self):
#     super().__init__('branch flags')
#     self.oe_skip = Signal(self, 1)
#     self.flags = Signal(self, 4)
#     self.mode = Signal(self, 4)
#     self.ie_skip = Signal(self, 1)
#     self.skip = Signal(self, 1)

#   def update(self):
#     pass

# class IoPort(Component):
#   def __init__(self):
#     super().__init__('io port')
#     self.mode = Signal(self, 1)
#     self.ie = Signal(self, 1)
#     self.oe = Signal(self, 1)
#     self.data = Signal(self, 8)
#     self.inp = Signal(self, 8)
#     self.out = Signal(self, 8)

#   def update(self):
#     pass

# class MemControl(Component):
#   def __init__(self):
#     super().__init__('mem ctrl')
#     self.addr_l = Signal(self, 8)
#     self.addr_h = Signal(self, 8)
#     self.ie = Signal(self, 1)
#     self.oe = Signal(self, 1)
#     self.ie_ram = Signal(self, 1)
#     self.ie_video = Signal(self, 1)
#     self.ie_io = Signal(self, 1)
#     self.oe_ram = Signal(self, 1)
#     self.oe_io = Signal(self, 1)
#     self.io_mode = Signal(self, 1)

#   def update(self):
#     self.io_mode.drive(self.addr_l.v & 1)
#     if self.ie.v:
#       if self.addr_h.v == 0 and self.addr_l.v < 2:
#         self.ie_io.drive(1)
#         self.ie_ram.drive(0)
#       else:
#         self.ie_io.drive(0)
#         self.ie_ram.drive(1)
#     else:
#       self.ie_io.drive(0)
#       self.ie_ram.drive(0)

#     if self.oe.v:
#       if self.addr_h.v == 0 and self.addr_l.v < 2:
#         self.oe_io.drive(1)
#         self.oe_ram.drive(0)
#       else:
#         self.oe_io.drive(0)
#         self.oe_ram.drive(1)
#     else:
#       self.oe_io.drive(0)
#       self.oe_ram.drive(0)




def main():
  power = Power()
  logic = Logic()
  reg_a = Register('reg_a')
  reg_b = Register('reg_b')
  reg_c = Register('reg_c')
  reg_d = Register('reg_d')
  reg_e = Register('reg_e')
  reg_f = Register('reg_f')
  reg_g = Register('reg_g')
  reg_h = Register('reg_h')
  reg_t = Register('reg_t')
  bus_a_b = BusConnect('ab')
  bus_a_t = BusConnect('at')
  dec = Decoder()
  #decoder_a = DecoderA()
  #decoder_b = DecoderB()
  ir = InstructionRegister()
  pc_l = ProgramCounter('l')
  pc_h = ProgramCounter('h')
  #branch_flags = BranchFlags()
  #io = IoPort()
  #mc = MemControl()
  ram = Ram()
  rom = Rom()
  clk = Clock(2)

  # Register busses
  reg_a.data += reg_c.data + reg_e.data + reg_g.data + bus_a_b.a# + logic.a + pc_l.data + ram.addr[0:8] + bus_a_b.a + bus_a_t.a
  reg_b.data += reg_d.data + reg_f.data + reg_h.data + bus_a_b.b# + logic.b + pc_h.data + ram.addr[8:16] + bus_a_b.b
  #logic.out += ram.data + reg_t.data + bus_a_t.b
  reg_a.data += ir.imm

  # Program counter
  pc_l.inc += dec.pc_inc
  pc_h.inc += pc_l.co

  # Instruction
  rom.oe += power.high
  rom.addr[0:8] += pc_l.addr
  rom.addr[8:16] += pc_h.addr
  ir.data += rom.data
  ir.ie += dec.ir_ie
  ir.oe += dec.ir_oe

  # Decoder
  dec.instr += ir.instr
  dec.clk += clk.clk

  # Register enable
  reg_a.ie += dec.a_ie
  reg_b.ie += dec.b_ie
  reg_c.ie += dec.c_ie
  reg_d.ie += dec.d_ie
  bus_a_b.a_to_b += dec.a_to_b
  bus_a_b.b_to_a += dec.b_to_a

  rom.rom[0] = Inst.load('al', 1)
  rom.rom[1] = Inst.load('ah', 2)
  rom.rom[2] = Inst.load('bl', 3)
  rom.rom[3] = Inst.load('bh', 4)
  rom.rom[4] = Inst.load('cl', 5)
  rom.rom[5] = Inst.load('ch', 6)
  rom.rom[6] = Inst.load('dl', 7)
  rom.rom[7] = Inst.load('dh', 8)

  print('ROM:')
  for i in range(0, 256, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in rom.rom[i:i+16])))

  for c in (
      power,
      logic,
      reg_a, reg_b, reg_c, reg_d, reg_e, reg_f, reg_g, reg_h,
      bus_a_b, bus_a_t,
      dec,
      ir,
      pc_l, pc_h,
      #branch_flags, io, mc,
      ram, rom,
      clk):
    c.reset()

  try:
    for i in range(8):
      for i in range(3 if i == 0 else 4):
        clk.tick()
      print('PC: 0x{:02x}{:02x} T: 0x{:02x}'.format(pc_h.addr.value(), pc_l.addr.value(), reg_t.data.value()))
      print('A: 0x{:02x} B: 0x{:02x} C: 0x{:02x} D: 0x{:02x} E: 0x{:02x} F: 0x{:02x} G: 0x{:02x} H: 0x{:02x}'.format(reg_a.value(), reg_b.value(), reg_c.value(), reg_d.value(), reg_e.value(), reg_f.value(), reg_g.value(), reg_h.value()))
  except KeyboardInterrupt:
    pass

  print('RAM:')
  for i in range(0, 256, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in ram.ram[i:i+16])))

if __name__ == '__main__':
  main()
