import sys
from sim import Component, Signal, Register, BusConnect, Clock, Ram, Rom, Power

# 0ddnxxxx  load imm dd=A,B,C,D n=h/l xxxx=data
# 10sssddd  mov sss to ddd  rrr=A,B,C,D,E,F,G,H
# 110ffffd  ALU ffff to dest d (A or C)
# 1110rrwa  r/w mem rr=A,B,E,F a=(C:D, G:H)
# 1111attt  jump a=(C:D, G:H)


class Assembler:
  IMM_REGISTERS = ('a', 'b', 'c', 'd',)
  MEM_REGISTERS = ('a', 'b', 'e', 'f',)
  IMM16_REGISTERS = ('a:b', 'c:d',)
  MOV_REGISTERS = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',)
  MOV16_REGISTERS = ('a:b', 'c:d', 'e:f', 'g:h',)
  ALU_REGISTERS = ('a', 'c',)
  LABEL_REGISTERS = ('a:b', 'c:d',)
  ADDR_REGISTERS = ('c:d', 'g:h',)

  PREFIX_IMM = 0
  PREFIX_MOV = 1<<7
  PREFIX_ALU = 1<<7 | 1<<6
  PREFIX_MEM = 1<<7 | 1<<6 | 1<<5
  PREFIX_JMP = 1<<7 | 1<<6 | 1<<5 | 1<<4

  MEM_READ = 0
  MEM_WRITE = 1<<1

  def __init__(self, rom, addr):
    self.rom = rom
    self.addr = addr
    self.labels = set()

  class Label:
    def __init__(self):
      self.addr = 0
      self.fixups = []

  def write(self, instr):
    self.rom.rom[self.addr] = instr
    self.addr += 1

  def __enter__(self):
    return self

  def __exit__(self, a, b, c):
    for l in self.labels:
      for f in l.fixups:
        f()

  def label(self, l):
    l.addr = self.addr

  def placeholder(self, n, label, fixup):
    self.labels.add(label)
    a = Assembler(self.rom, self.addr)
    label.fixups.append(lambda: fixup(a))
    self.addr += n

  def load8(self, reg, v):
    reg = reg.lower()
    if reg not in Assembler.IMM_REGISTERS:
      raise ValueError(f'Invalid register for load8: {reg}.')
    self.load(reg + 'h', (v >> 4) & 0xf)
    self.load(reg + 'l', v & 0xf)

  def load16(self, reg, v):
    reg = reg.lower()
    if reg not in Assembler.IMM16_REGISTERS:
      raise ValueError(f'Invalid register for load16: {reg}.')
    self.load(reg[0] + 'h', (v >> 12) & 0xf)
    self.load(reg[0] + 'l', (v >> 8) & 0xf)
    self.load(reg[2] + 'h', (v >> 4) & 0xf)
    self.load(reg[2] + 'l', v & 0xf)

  def loadlabel(self, reg, label):
    reg = reg.lower()
    if reg not in Assembler.LABEL_REGISTERS:
      raise ValueError(f'Invalid register for load label: {reg}.')
    def fixup(a):
      a.load16(reg, label.addr)
    self.placeholder(4, label, fixup)

  def load(self, reg, nibble):
    reg = reg.lower()
    if len(reg) != 2 or reg[0] not in Assembler.IMM_REGISTERS or reg[1] not in ('l', 'h',):
      raise ValueError(f'Invalid register for load: {reg}.')
    index = ord(reg[0]) - ord('a')
    self.write(Assembler.PREFIX_IMM | (nibble) | (0b10000 if reg[1] == 'h' else 0) | (index << 5))

  def mov(self, dst, src):
    dst = dst.lower()
    src = src.lower()
    if dst not in Assembler.MOV_REGISTERS:
      raise ValueError(f'Invalid destination register: {dst}')
    if src not in Assembler.MOV_REGISTERS:
      raise ValueError(f'Invalid source register: {src}')
    self.write(Assembler.PREFIX_MOV | ((ord(src) - ord('a'))<<3) | (ord(dst) - ord('a')))

  def mov16(self, dst, src):
    dst = dst.lower()
    src = src.lower()
    if dst not in Assembler.MOV16_REGISTERS:
      raise ValueError(f'Invalid destination register: {dst}')
    if src not in Assembler.MOV16_REGISTERS:
      raise ValueError(f'Invalid source register: {src}')
    self.mov(dst[0], src[0])
    self.mov(dst[2], src[2])

  def alu(self, dst, fn):
    dst = dst.lower()
    if dst not in Assembler.ALU_REGISTERS:
      raise ValueError(f'Invalid destination register for ALU: {reg}.')
    if fn > 15:
      raise ValueError(f'Invalid ALU function: {fn}.')
    self.write(Assembler.PREFIX_ALU | (fn << 1) | (0 if dst == 'a' else 1))

  def add(self, dst):
    self.alu(dst, 0)

  def sub(self, dst):
    self.alu(dst, 1)

  def jmp(self, addr='c:d'):
    addr = addr.lower()
    if addr not in Assembler.ADDR_REGISTERS:
      raise ValueError(f'Invalid jump register: {addr}.')
    self.write(Assembler.PREFIX_JMP | (Assembler.ADDR_REGISTERS.index(addr) << 3) | 0)

  def rmem(self, dst='a', addr='c:d'):
    # 1110rrwa  r/w mem rr=A,B,E,F a=(C:D, G:H)
    dst = dst.lower()
    addr = addr.lower()
    if dst not in Assembler.MEM_REGISTERS:
      raise ValueError(f'Invalid mem dst register: {dst}.')
    if addr not in Assembler.ADDR_REGISTERS:
      raise ValueError(f'Invalid addr register: {addr}.')
    self.write(Assembler.PREFIX_MEM | (Assembler.MEM_REGISTERS.index(dst) << 2) | Assembler.MEM_READ | Assembler.ADDR_REGISTERS.index(addr))

  def wmem(self, src='a', addr='c:d'):
    src = src.lower()
    addr = addr.lower()
    if src not in Assembler.MEM_REGISTERS:
      raise ValueError(f'Invalid mem src register: {dst}.')
    if addr not in Assembler.ADDR_REGISTERS:
      raise ValueError(f'Invalid addr register: {addr}.')
    self.write(Assembler.PREFIX_MEM | (Assembler.MEM_REGISTERS.index(src) << 2) | Assembler.MEM_WRITE | Assembler.ADDR_REGISTERS.index(addr))


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

    self.sel_cd = Signal(self, 'sel_cd', 1)
    self.sel_gh = Signal(self, 'sel_gh', 1)

    self.mem_ie = Signal(self, 'mem_ie', 1)
    self.mem_oe = Signal(self, 'mem_oe', 1)

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

    sel_cd = 0
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
    is_mem_read = is_mem & ~((instr >> 1) & 1)
    is_mem_write = is_mem & ((instr >> 1) & 1)
    sel_cd |= m3 & is_mem & ~(instr & 1)
    sel_gh |= m3 & is_mem & (instr & 1)
    mem_reg = (instr >> 2) & 3
    a_oe |= m1 & is_mem_write & (mem_reg == 0)
    b_oe |= m1 & is_mem_write & (mem_reg == 1)
    e_oe |= m1 & is_mem_write & (mem_reg == 2)
    f_oe |= m1 & is_mem_write & (mem_reg == 3)
    a_ie |= m4 & is_mem_read & (mem_reg == 0)
    b_ie |= m4 & is_mem_read & (mem_reg == 1)
    e_ie |= m4 & is_mem_read & (mem_reg == 2)
    f_ie |= m4 & is_mem_read & (mem_reg == 3)

    t_ie |= m2 & is_mem
    t_oe |= m3 & is_mem

    self.mem_ie <<= m4 & is_mem_write
    self.mem_oe <<= m1 & is_mem_read

    # JMP
    is_jmp = b7 and b6 and b5 and b4
    self.pc_inc <<= m4 & ~is_jmp  # Not jump
    self.pc_ie <<= m4 & is_jmp
    sel_cd |= m3 & is_jmp & ~((instr >> 3) & 1)
    sel_gh |= m3 & is_jmp & ((instr >> 3) & 1)

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

    self.sel_cd <<= sel_cd
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
      #print('Jump')
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
  sel_cd = BusConnect('sel_cd', width=16)
  sel_gh = BusConnect('sel_gh', width=16)
  ram = Ram()
  rom = Rom()
  clk = Clock(2)

  # Register bus
  reg_a.data += reg_b.data + reg_c.data + reg_d.data + reg_e.data + reg_f.data + reg_g.data + reg_h.data + reg_t.data + logic.out + ir.imm + ram.data

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
  sel_cd.a[0:8] += reg_d.state
  sel_cd.a[8:16] += reg_c.state
  sel_gh.a[0:8] += reg_h.state
  sel_gh.a[8:16] += reg_g.state
  pc_l.data += sel_cd.b[0:8] + sel_gh.b[0:8] + ram.addr[0:8]
  pc_h.data += sel_cd.b[8:16] + sel_gh.b[8:16] + ram.addr[8:16]
  sel_cd.a_to_b += dec.sel_cd
  sel_gh.a_to_b += dec.sel_gh

  ram.ie += dec.mem_ie
  ram.oe += dec.mem_oe

  n = 0
  with Assembler(rom, 0) as a:
    a.load('al', 1)
    a.load('ah', 2)
    a.load('bl', 3)
    a.load('bh', 4)
    a.load('cl', 5)
    a.load('ch', 6)
    a.load('dl', 7)
    a.load('dh', 8)

    a.mov('e', 'a')
    a.mov('f', 'b')
    a.mov('g', 'c')
    a.mov('h', 'd')

    a.add('a')
    a.add('c')
    a.sub('a')
    a.sub('c')

    a.load16('c:d', 0x10)
    a.mov16('g:h', 'c:d')
    a.load16('c:d', 0x20)
    a.load8('a', 0x23)
    a.wmem('a', 'c:d')
    a.load8('a', 0x45)
    a.mov('e', 'a')
    a.wmem('e', 'g:h')

    l1 = Assembler.Label()
    l2 = Assembler.Label()

    a.load8('a', 0)
    a.load8('b', 1)
    a.load16('c:d', 0x80)
    a.mov16('g:h', 'c:d')
    a.loadlabel('c:d', l2)

    n = a.addr
    a.label(l2)
    a.add('a')
    a.wmem('a', 'g:h')
    a.mov('e', 'a')
    a.mov('a', 'h')
    a.add('a')
    a.mov('h', 'a')
    a.mov('a', 'e')
    a.jmp('c:d')

    n = n + (a.addr - n)*32

  print('ROM:')
  for i in range(0, 256, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in rom.rom[i:i+16])))

  for c in (
      power,
      logic,
      reg_a, reg_b, reg_c, reg_d, reg_e, reg_f, reg_g, reg_h,
      reg_t,
      sel_cd, sel_gh,
      dec,
      ir,
      pc_l, pc_h,
      ram, rom,
      clk):
    c.reset()

  try:
    for i in range(n):
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
