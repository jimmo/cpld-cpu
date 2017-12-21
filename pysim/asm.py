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
    self.alu(dst, 4)

  def sub(self, dst):
    self.alu(dst, 5)

  def inc(self, dst):
    self.alu(dst, 9)

  def dec(self, dst):
    self.alu(dst, 10)

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
