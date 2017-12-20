import sys
from sim import Component, Signal, Register, BusConnect, Clock, Ram, Rom, Power

# 0ddnxxxx  load imm dd=A,B,C,D n=h/l xxxx=data
# 10sssddd  mov sss to ddd  rrr=A,B,C,D,E,F,G,H
# 110ffffd  ALU ffff to dest d (A or C)
# 1110?wtt  r/w mem tt=(C:D, E:F, E:F, G:H) read=(B,B,D,D), write=(A,A,C,C)
# 1111rttt  jump r=(E:F, G:H)


class Inst:
  IMM_REGISTERS = ('a', 'b', 'c', 'd',)
  REGISTERS = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',)
  ALU_REGISTERS = ('a', 'c')

  PREFIX_IMM = 0
  PREFIX_MOV = 1<<7
  PREFIX_ALU = 1<<7 | 1<<6
  PREFIX_MEM = 1<<7 | 1<<6 | 1<<5
  PREFIX_JMP = 1<<7 | 1<<6 | 1<<5 | 1<<4

  @classmethod
  def load(cls, reg, nibble):
    reg = reg.lower()
    if len(reg) != 2 or reg[0] not in Inst.IMM_REGISTERS or reg[1] not in ('l', 'h',):
      raise ValueError(f'Invalid register for load: {reg}.')
    index = ord(reg[0]) - ord('a')
    return Inst.PREFIX_IMM | (nibble) | (0b10000 if reg[1] == 'h' else 0) | (index << 5)

  @classmethod
  def mov(cls, dst, src):
    dst = dst.lower()
    src = src.lower()
    if dst not in Inst.REGISTERS:
      raise ValueError(f'Invalid destination register: {dst}')
    if src not in Inst.REGISTERS:
      raise ValueError(f'Invalid source register: {src}')
    return Inst.PREFIX_MOV | ((ord(src) - ord('a'))<<3) | (ord(dst) - ord('a'))

  @classmethod
  def alu(cls, dst, fn):
    dst = dst.lower()
    if dst not in Inst.ALU_REGISTERS:
      raise ValueError(f'Invalid destination register for ALU: {reg}.')
    if fn > 15:
      raise ValueError(f'Invalid ALU function: {fn}.')
    return Inst.PREFIX_ALU | (fn << 1) | (0 if dst == 'a' else 1)

  @classmethod
  def add(cls, dst):
    return Inst.alu(dst, 0)

  @classmethod
  def sub(cls, dst):
    return Inst.alu(dst, 1)

  @classmethod
  def jmp(cls, dst='e:f'):
    return Inst.PREFIX_JMP | (1<<3 if dst=='g:h' else 0) | 0


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
        o = a  #
      elif fn == 13:
        o = a  #
      elif fn == 14:
        o = a  #
      elif fn == 15:
        o = a  #
      self.out <<= (o % 0x100)
    else:
      self.out <<= None
      self.flags <<= None


class Decoder(Component):
  def __init__(self):
    super().__init__('decoder')
    self.instr = Signal(self, 'instr', 8)
    self.clk = Signal(self, 'clk', 2)

    self.al_ie = Signal(self, 'al_ie', 1)
    self.ah_ie = Signal(self, 'ah_ie', 1)
    self.bl_ie = Signal(self, 'bl_ie', 1)
    self.bh_ie = Signal(self, 'bh_ie', 1)
    self.cl_ie = Signal(self, 'cl_ie', 1)
    self.ch_ie = Signal(self, 'ch_ie', 1)
    self.dl_ie = Signal(self, 'dl_ie', 1)
    self.dh_ie = Signal(self, 'dh_ie', 1)
    self.e_ie = Signal(self, 'e_ie', 1)
    self.f_ie = Signal(self, 'f_ie', 1)
    self.g_ie = Signal(self, 'g_ie', 1)
    self.h_ie = Signal(self, 'h_ie', 1)
    self.t_ie = Signal(self, 't_ie', 1)

    self.a_oe = Signal(self, 'a_oe', 1)
    self.b_oe = Signal(self, 'b_oe', 1)
    self.c_oe = Signal(self, 'c_oe', 1)
    self.d_oe = Signal(self, 'd_oe', 1)
    self.e_oe = Signal(self, 'e_oe', 1)
    self.f_oe = Signal(self, 'f_oe', 1)
    self.g_oe = Signal(self, 'g_oe', 1)
    self.h_oe = Signal(self, 'h_oe', 1)

    self.t_oe = Signal(self, 't_oe', 1)

    self.pc_inc = Signal(self, 'pc_inc', 1)
    self.pc_ie = Signal(self, 'pc_ie', 1)

    self.ir_ie = Signal(self, 'ir_ie', 1)
    self.ir_oe = Signal(self, 'ir_oe', 1)

    self.alu_fn = Signal(self, 'alu_fn', 4)
    self.alu_oe = Signal(self, 'alu_oe', 1)


    self.sel_ef = Signal(self, 'sel_ef', 1)
    self.sel_gh = Signal(self, 'sel_gh', 1)

  def reset(self):
    self.pc_inc <<= 0

  def update(self, signal):
    m1 = self.clk.value() <= 1
    m2 = self.clk.value() == 1
    m3 = self.clk.value() >= 2
    m4 = self.clk.value() == 3
    #print('m1' if m1 else '', 'm2' if m2 else '', 'm3' if m3 else '', 'm4' if m4 else '')

    self.ir_ie <<= m1

    instr = self.instr.value()

    b7 = ((instr >> 7) & 1)
    b6 = ((instr >> 6) & 1)
    b5 = ((instr >> 5) & 1)
    b4 = ((instr >> 4) & 1)

    a_ie = 0
    b_ie = 0
    c_ie = 0
    d_ie = 0
    e_ie = 0
    f_ie = 0
    g_ie = 0
    h_ie = 0

    a_oe = 0
    b_oe = 0
    c_oe = 0
    d_oe = 0
    e_oe = 0
    f_oe = 0
    g_oe = 0
    h_oe = 0

    t_ie = 0
    t_oe = 0

    sel_ef = 0
    sel_gh = 0

    # IMM
    is_imm = not b7
    is_imm_high = ((instr >> 4) & 1)
    imm_dest = ((instr >> 5) & 3)
    self.ir_oe <<= (m3 & is_imm)

    # MOV
    is_mov = b7 and not b6
    mov_src = ((instr >> 3) & 7)
    mov_dst = (instr & 7)

    a_oe |= m1 & is_mov & (mov_src == 0)
    b_oe |= m1 & is_mov & (mov_src == 1)
    c_oe |= m1 & is_mov & (mov_src == 2)
    d_oe |= m1 & is_mov & (mov_src == 3)
    e_oe |= m1 & is_mov & (mov_src == 4)
    f_oe |= m1 & is_mov & (mov_src == 5)
    g_oe |= m1 & is_mov & (mov_src == 6)
    h_oe |= m1 & is_mov & (mov_src == 7)

    a_ie |= m4 & is_mov & (mov_dst == 0)
    b_ie |= m4 & is_mov & (mov_dst == 1)
    c_ie |= m4 & is_mov & (mov_dst == 2)
    d_ie |= m4 & is_mov & (mov_dst == 3)
    e_ie |= m4 & is_mov & (mov_dst == 4)
    f_ie |= m4 & is_mov & (mov_dst == 5)
    g_ie |= m4 & is_mov & (mov_dst == 6)
    h_ie |= m4 & is_mov & (mov_dst == 7)

    t_ie |= m2 & is_mov
    t_oe |= m3 & is_mov

    # ALU
    is_alu = b7 and b6 and not b5
    self.alu_fn <<= (instr >> 1) & 0xf
    self.alu_oe <<= m1 & is_alu
    t_ie |= m2 & is_alu
    t_oe |= m3 & is_alu
    a_ie |= m4 & is_alu & ~(instr & 1)
    c_ie |= m4 & is_alu & (instr & 1)

    # MEM
    is_mem = b7 and b6 and b5 and not b4

    # JMP
    is_jmp = b7 and b6 and b5 and b4
    self.pc_inc <<= m4 & ~is_jmp  # Not jump
    self.pc_ie <<= m4 & is_jmp
    sel_ef |= m3 & ~((instr >> 3) & 1)
    sel_gh |= m3 & ((instr >> 3) & 1)

    # Set ie/oe lines.
    self.al_ie <<= a_ie | ((m4 & is_imm & (imm_dest == 0)) & ~is_imm_high)
    self.ah_ie <<= a_ie | ((m4 & is_imm & (imm_dest == 0)) & is_imm_high)
    self.bl_ie <<= b_ie | ((m4 & is_imm & (imm_dest == 1)) & ~is_imm_high)
    self.bh_ie <<= b_ie | ((m4 & is_imm & (imm_dest == 1)) & is_imm_high)
    self.cl_ie <<= c_ie | ((m4 & is_imm & (imm_dest == 2)) & ~is_imm_high)
    self.ch_ie <<= c_ie | ((m4 & is_imm & (imm_dest == 2)) & is_imm_high)
    self.dl_ie <<= d_ie | ((m4 & is_imm & (imm_dest == 3)) & ~is_imm_high)
    self.dh_ie <<= d_ie | ((m4 & is_imm & (imm_dest == 3)) & is_imm_high)
    self.e_ie <<= e_ie
    self.f_ie <<= f_ie
    self.g_ie <<= g_ie
    self.h_ie <<= h_ie

    self.a_oe <<= a_oe
    self.b_oe <<= b_oe
    self.c_oe <<= c_oe
    self.d_oe <<= d_oe
    self.e_oe <<= e_oe
    self.f_oe <<= f_oe
    self.g_oe <<= g_oe
    self.h_oe <<= h_oe

    self.t_ie <<= t_ie
    self.t_oe <<= t_oe

    self.sel_ef <<= sel_ef
    self.sel_gh <<= sel_gh


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
      print('Jump')
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
  reg_a = Register('reg_a', load_width=4)
  reg_b = Register('reg_b', load_width=4)
  reg_c = Register('reg_c', load_width=4)
  reg_d = Register('reg_d', load_width=4)
  reg_e = Register('reg_e')
  reg_f = Register('reg_f')
  reg_g = Register('reg_g')
  reg_h = Register('reg_h')
  reg_t = Register('reg_t')
  dec = Decoder()
  ir = InstructionRegister()
  pc_l = ProgramCounter('l')
  pc_h = ProgramCounter('h')
  sel_ef = BusConnect('sel_ef', width=16)
  sel_gh = BusConnect('sel_gh', width=16)
  ram = Ram()
  rom = Rom()
  clk = Clock(2)

  # Register bus
  reg_a.data += reg_b.data + reg_c.data + reg_d.data + reg_e.data + reg_f.data + reg_g.data + reg_h.data + reg_t.data + logic.out + ir.imm

  # Program counter
  pc_l.inc += dec.pc_inc
  pc_h.inc += pc_l.co
  pc_l.ie += dec.pc_ie
  pc_h.ie += dec.pc_ie

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
  reg_a.ie[0] += dec.al_ie
  reg_a.ie[1] += dec.ah_ie
  reg_b.ie[0] += dec.bl_ie
  reg_b.ie[1] += dec.bh_ie
  reg_c.ie[0] += dec.cl_ie
  reg_c.ie[1] += dec.ch_ie
  reg_d.ie[0] += dec.dl_ie
  reg_d.ie[1] += dec.dh_ie
  reg_e.ie += dec.e_ie
  reg_f.ie += dec.f_ie
  reg_g.ie += dec.g_ie
  reg_h.ie += dec.h_ie
  reg_t.ie += dec.t_ie

  reg_a.oe += dec.a_oe
  reg_b.oe += dec.b_oe
  reg_c.oe += dec.c_oe
  reg_d.oe += dec.d_oe
  reg_e.oe += dec.e_oe
  reg_f.oe += dec.f_oe
  reg_g.oe += dec.g_oe
  reg_h.oe += dec.h_oe
  reg_t.oe += dec.t_oe

  # Logic
  logic.fn += dec.alu_fn
  logic.oe += dec.alu_oe
  logic.a += reg_a.state
  logic.b += reg_b.state

  # Memory
  sel_ef.a[0:8] += reg_f.state
  sel_ef.a[8:16] += reg_e.state
  sel_gh.a[0:8] += reg_h.state
  sel_gh.a[8:16] += reg_g.state
  pc_l.data += sel_ef.b[0:8] + sel_gh.b[0:8]
  pc_h.data += sel_ef.b[8:16] + sel_gh.b[8:16]
  sel_ef.a_to_b += dec.sel_ef
  sel_gh.a_to_b += dec.sel_gh

  with rom.write(0) as w:
    w.next(Inst.load('al', 1))
    w.next(Inst.load('ah', 2))
    w.next(Inst.load('bl', 3))
    w.next(Inst.load('bh', 4))
    w.next(Inst.load('cl', 5))
    w.next(Inst.load('ch', 6))
    w.next(Inst.load('dl', 7))
    w.next(Inst.load('dh', 8))

    w.next(Inst.mov('e', 'a'))
    w.next(Inst.mov('f', 'b'))
    w.next(Inst.mov('g', 'c'))
    w.next(Inst.mov('h', 'd'))

    w.next(Inst.add('a'))
    w.next(Inst.add('c'))
    w.next(Inst.sub('a'))
    w.next(Inst.sub('c'))

    w.next(Inst.load('al', 0))
    w.next(Inst.load('ah', 0))
    w.next(Inst.load('bl', 1))
    w.next(Inst.load('bh', 0))
    w.next(Inst.load('cl', 0))
    w.next(Inst.load('ch', 0))
    w.next(Inst.mov('e', 'c'))
    w.next(Inst.mov('g', 'c'))
    w.next(Inst.load('cl', 0xd))
    w.next(Inst.load('ch', 1))
    w.next(Inst.mov('f', 'c'))
    w.next(Inst.load('cl', 0xe))
    w.next(Inst.mov('h', 'c'))
    w.next(Inst.add('a'))
    w.next(Inst.add('a'))
    w.next(Inst.jmp('g:h'))

  print('ROM:')
  for i in range(0, 256, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in rom.rom[i:i+16])))

  for c in (
      power,
      logic,
      reg_a, reg_b, reg_c, reg_d, reg_e, reg_f, reg_g, reg_h,
      reg_t,
      dec,
      ir,
      pc_l, pc_h,
      ram, rom,
      clk):
    c.reset()

  try:
    for i in range(40):
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
