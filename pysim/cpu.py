import sys
from sim import Component, Signal, NotifySignal, Register, SplitRegister, BusConnect, Clock, Ram, Rom, Power
from asm import Assembler


class Logic(Component):
  def __init__(self):
    super().__init__('logic')
    self.a = NotifySignal(self, 'a', 8)
    self.b = NotifySignal(self, 'b', 8)
    self.fn = NotifySignal(self, 'fn', 4)
    self.out = Signal(self, 'out', 8)
    self.fi = NotifySignal(self, 'fi', 4)
    self.fo = Signal(self, 'fo', 4)
    self.oe = NotifySignal(self, 'oe', 1)

    # c = carry
    # z = zero
    # n = negative
    # v = overflow

  def update(self, signal):
    if self.oe.value():
      a = self.a.value()
      b = self.b.value()
      flags = self.fi.value()
      c = (flags >> 3) & 1
      v = (flags >> 2) & 1
      n = (flags >> 1) & 1
      z = (flags >> 0) & 1
      o = 0
      of = None
      calc_flags = True
      fn = self.fn.value()

      if fn == 0:
        # not, cznv
        o = ~a
      elif fn == 1:
        # xor, znv
        o = a ^ b
      elif fn == 2:
        # or, znv
        o = a | b
      elif fn == 3:
        # and, znv
        o = a & b
      elif fn == 4:
        # add, cznv
        o = a + b + c
      elif fn == 5:
        # sub, cznv
        o = a - b - c
      elif fn == 6:
        # cmp, cznv
        # a - b - c?
        o = a
        of = a - b
      elif fn == 7:
        # shl, cznv
        o = a << 1
      elif fn == 8:
        # shr, cznv
        o = a >> 1
      elif fn == 9:
        # inc, znv
        o = a + 1
      elif fn == 10:
        # dec, znv
        o = a - 1
      elif fn == 11:
        # neg, cznv
        o = -a
      elif fn == 12:
        # clf, cznv
        o = a
        c = 0
        z = 0
        n = 0
        v = 0
        calc_flags = False
      elif fn == 13:
        # inv, cvnz
        o = a
        c = 1-c
        z = 1-z
        n = 1-n
        v = 1-v
        calc_flags = False
      elif fn == 14:
        # rol, c=a[7], znv
        o = (a << 1) | c
      elif fn == 15:
        # ror, c=a[0], znv
        o = (a >> 1) | (c << 7)


      if calc_flags:
        if of is None:
          of = o
        c = of > 0xff
        z = of == 0
        v = 0  # TODO: signed
        n = 0  # TODO: signed

      self.out <<= (o & 0xff)
      self.fo <<= (c<<3) | (v<<2) | (n<<1) | (z<<0)
    else:
      self.out <<= None
      self.fo <<= None


class Decoder(Component):
  def __init__(self):
    super().__init__('decoder')
    self.instr = NotifySignal(self, 'instr', 8)
    self.flags = NotifySignal(self, 'flags', 4)
    self.clk = NotifySignal(self, 'clk', 2)

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

    self.flags_ie = Signal(self, 'flags_ie', 1)
    self.flags_tmp_ie = Signal(self, 'flags_tmp_ie', 1)

  def reset(self):
    self.pc_inc <<= 0

  def update(self, signal):
    clk = self.clk.value()
    m1 = clk <= 1
    m2 = clk == 1
    m3 = clk >= 2
    m4 = clk == 3
    #print('m1' if m1 else '', 'm2' if m2 else '', 'm3' if m3 else '', 'm4' if m4 else '')

    self.ir_ie <<= m1
    self.flags_ie <<= m1

    instr = self.instr.value()

    flags = self.flags.value()
    c = (flags >> 3) & 1
    v = (flags >> 2) & 1
    n = (flags >> 1) & 1
    z = (flags >> 0) & 1

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

    flags_tmp_ie = 0

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
    mov_oe = m1 & is_mov
    mov_ie = m4 & is_mov

    a_oe |= mov_oe & (mov_src == 0)
    b_oe |= mov_oe & (mov_src == 1)
    c_oe |= mov_oe & (mov_src == 2)
    d_oe |= mov_oe & (mov_src == 3)
    e_oe |= mov_oe & (mov_src == 4)
    f_oe |= mov_oe & (mov_src == 5)
    g_oe |= mov_oe & (mov_src == 6)
    h_oe |= mov_oe & (mov_src == 7)

    a_ie |= mov_ie & (mov_dst == 0)
    b_ie |= mov_ie & (mov_dst == 1)
    c_ie |= mov_ie & (mov_dst == 2)
    d_ie |= mov_ie & (mov_dst == 3)
    e_ie |= mov_ie & (mov_dst == 4)
    f_ie |= mov_ie & (mov_dst == 5)
    g_ie |= mov_ie & (mov_dst == 6)
    h_ie |= mov_ie & (mov_dst == 7)

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
    flags_tmp_ie |= m2 & is_alu

    # MEM
    is_mem = b7 and b6 and b5 and not b4
    is_mem_read = is_mem & ~((instr >> 1) & 1)
    is_mem_write = is_mem & ((instr >> 1) & 1)
    sel_cd |= is_mem & ~(instr & 1)
    sel_gh |= is_mem & (instr & 1)
    mem_reg = (instr >> 2) & 3
    mem_reg_oe = m1 & is_mem_write
    mem_reg_ie = m4 & is_mem_read

    a_oe |= mem_reg_oe & (mem_reg == 0)
    b_oe |= mem_reg_oe & (mem_reg == 1)
    e_oe |= mem_reg_oe & (mem_reg == 2)
    f_oe |= mem_reg_oe & (mem_reg == 3)
    a_ie |= mem_reg_ie & (mem_reg == 0)
    b_ie |= mem_reg_ie & (mem_reg == 1)
    e_ie |= mem_reg_ie & (mem_reg == 2)
    f_ie |= mem_reg_ie & (mem_reg == 3)

    t_ie |= m2 & is_mem
    t_oe |= m3 & is_mem

    self.mem_ie <<= m4 & is_mem_write
    self.mem_oe <<= m1 & is_mem_read

    # JMP
    is_jmp = b7 and b6 and b5 and b4
    # jmp, jz, jn, jls, jc, jo
    jmp_type = (instr & 7)
    do_jmp = is_jmp & ((jmp_type == 0) | (jmp_type == 1 and z == 1) | (jmp_type == 2 and n == 1) | (jmp_type == 3 and (n ^ v) == 1) | (jmp_type == 4 and c == 1) | (jmp_type == 5 and v == 1))
    self.pc_inc <<= m4 & ~do_jmp  # Increment if not jump
    self.pc_ie <<= m4 & do_jmp    # Load PC if jump
    sel_cd |= m3 & do_jmp & ~((instr >> 3) & 1)
    sel_gh |= m3 & do_jmp & ((instr >> 3) & 1)

    # Set ie/oe lines.
    imm_ie_l = m4 & is_imm & ~is_imm_high
    imm_ie_h = m4 & is_imm & is_imm_high
    self.al_ie <<= a_ie | (imm_ie_l & (imm_dest == 0))
    self.ah_ie <<= a_ie | (imm_ie_h & (imm_dest == 0))
    self.bl_ie <<= b_ie | (imm_ie_l & (imm_dest == 1))
    self.bh_ie <<= b_ie | (imm_ie_h & (imm_dest == 1))
    self.cl_ie <<= c_ie | (imm_ie_l & (imm_dest == 2))
    self.ch_ie <<= c_ie | (imm_ie_h & (imm_dest == 2))
    self.dl_ie <<= d_ie | (imm_ie_l & (imm_dest == 3))
    self.dh_ie <<= d_ie | (imm_ie_h & (imm_dest == 3))
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

    self.flags_tmp_ie <<= flags_tmp_ie

    self.sel_cd <<= sel_cd
    self.sel_gh <<= sel_gh


class InstructionRegister(Component):
  def __init__(self):
    super().__init__('ir')
    self.v = 0
    self.data = Signal(self, 'data', 8)
    self.instr = Signal(self, 'instr', 8)
    self.imm = Signal(self, 'imm', 8)
    self.ie = NotifySignal(self, 'ie', 1)
    self.oe = NotifySignal(self, 'oe', 1)

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      self.v = self.data.value()
      self.instr <<= self.v
    if self.oe.value():
      imm = (self.v & 0xf)
      self.imm <<= (imm | (imm << 4))
    else:
      self.imm <<= None


class ProgramCounter(Component):
  def __init__(self, n):
    super().__init__('pc ' + n)
    self.v = 0
    self.addr = Signal(self, 'addr', 8)
    self.data = Signal(self, 'data', 8)
    self.rst = NotifySignal(self, 'rst', 1)
    self.inc = NotifySignal(self, 'inc', 1)
    self.ie = NotifySignal(self, 'ie', 1)
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


def main():
  power = Power()
  logic = Logic()
  reg_a = SplitRegister('reg_a', load_width=4)
  reg_b = SplitRegister('reg_b', load_width=4)
  reg_c = SplitRegister('reg_c', load_width=4)
  reg_d = SplitRegister('reg_d', load_width=4)
  reg_e = Register('reg_e')
  reg_f = Register('reg_f')
  reg_g = Register('reg_g')
  reg_h = Register('reg_h')
  reg_tmp = Register('reg_tmp')

  reg_flags = Register('reg_flags', width=4)
  reg_flags_tmp = Register('reg_flags_tmp', width=4)

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
  reg_a.data += reg_b.data + reg_c.data + reg_d.data + reg_e.data + reg_f.data + reg_g.data + reg_h.data + reg_tmp.data + logic.out + ir.imm + ram.data

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
  reg_tmp.ie += dec.t_ie

  reg_a.oe += dec.a_oe
  reg_b.oe += dec.b_oe
  reg_c.oe += dec.c_oe
  reg_d.oe += dec.d_oe
  reg_e.oe += dec.e_oe
  reg_f.oe += dec.f_oe
  reg_g.oe += dec.g_oe
  reg_h.oe += dec.h_oe
  reg_tmp.oe += dec.t_oe

  # Logic
  logic.fn += dec.alu_fn
  logic.oe += dec.alu_oe
  logic.a += reg_a.state
  logic.b += reg_b.state

  # Flags
  reg_flags.data += reg_flags_tmp.state
  reg_flags.ie += dec.flags_ie
  reg_flags.state += dec.flags + logic.fi
  reg_flags_tmp.data += logic.fo
  reg_flags_tmp.ie += dec.flags_tmp_ie

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
    if not a.parse(sys.argv[1]):
      return
    while a.addr < 0x100:
      a.mov('a', 'a')

  print('ROM:')
  for i in range(0, 256, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in rom.rom[i:i+16])))

  for c in (
      power,
      logic,
      reg_a, reg_b, reg_c, reg_d, reg_e, reg_f, reg_g, reg_h,
      reg_tmp,
      reg_flags, reg_flags_tmp,
      sel_cd, sel_gh,
      dec,
      ir,
      pc_l, pc_h,
      ram, rom,
      clk):
    c.info()
    c.reset()

  last_pc = None
  first_op = True

  try:
    while True:
      for i in range(3 if first_op else 4):
        clk.tick()
      first_op = False

      print('PC: 0x{:02x}{:02x} T: 0x{:02x} F: 0x{:02x} (0x{:02x})'.format(pc_h.addr.value(), pc_l.addr.value(), reg_tmp.value(), reg_flags.value(), reg_flags_tmp.value()))
      print('A: 0x{:02x} B: 0x{:02x} C: 0x{:02x} D: 0x{:02x} E: 0x{:02x} F: 0x{:02x} G: 0x{:02x} H: 0x{:02x}'.format(reg_a.value(), reg_b.value(), reg_c.value(), reg_d.value(), reg_e.value(), reg_f.value(), reg_g.value(), reg_h.value()))
      #print('RAM:')
      #for i in range(0, 256, 16):
      #  print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in ram.ram[i:i+16])))

      pc = (pc_h.addr.value() << 8) | pc_l.addr.value()
      if pc == last_pc:
        break
      last_pc = pc
  except KeyboardInterrupt:
    pass

  print('RAM:')
  for i in range(0, 256, 16):
    print('{:02x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in ram.ram[i:i+16])))

if __name__ == '__main__':
  main()
