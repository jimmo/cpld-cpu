# 0ddnxxxx  load imm dd=A,B,C,D n=h/l xxxx=data
# 10sssddd  mov sss to ddd  rrr=A,B,C,D,E,F,G,H
# 110ffffd  ALU ffff to dest d (A or C)
# 1110rrwa  r/w mem rr=A,B,E,F a=(C:D, G:H)
# 1111attt  jump a=(C:D, G:H)


import collections
from lark import Lark, Transformer
from lark.lexer import UnexpectedInput

l = Lark(open('asm.g').read())

class AssemblerTransformer(Transformer):
  def __init__(self, assembler):
    self.assembler = assembler
    self.labels = collections.defaultdict(Assembler.Label)

  def number(self, token):
    if token.type != 'NUMBER':
      raise ValueError(f'Invalid number token type {token.type} "{token}"')
    if token.startswith('0x'):
      return int(token, 16)
    if token.startswith('0o'):
      return int(token, 8)
    return int(token, 10)

  def op(self, m):
    if m[0].type == 'LABEL':
      l = self.labels[m[0]]
      l.name = m[0]
      self.assembler.label(l)
      m = m[1:]

    if m[0].type == 'OP_LOAD':
      self.assembler.load(m[1], self.number(m[2]))
    elif m[0].type == 'OP_LOAD8':
      self.assembler.load8(m[1], self.number(m[2]))
    elif m[0].type == 'OP_LOAD16':
      if m[2].type == 'LABEL':
        l = self.labels[m[2]]
        l.name = m[2]
        self.assembler.loadlabel(m[1], l)
      else:
        self.assembler.load16(m[1], self.number(m[2]))
    elif m[0].type == 'OP_MOV':
      self.assembler.mov(m[1], m[2])
    elif m[0].type == 'OP_MOV16':
      self.assembler.mov16(m[1], m[2])
    elif m[0].type == 'OP_ALU':
      getattr(self.assembler, 'alu_' + m[0])(m[1])
    elif m[0].type == 'OP_ALU_NOP':
      getattr(self.assembler, 'alu_' + m[0])()
    elif m[0].type == 'OP_RMEM':
      self.assembler.rmem(m[1], m[2])
    elif m[0].type == 'OP_WMEM':
      self.assembler.wmem(m[1], m[2])
    elif m[0].type == 'OP_JMP':
      getattr(self.assembler, 'jmp_' + m[0])(m[1])
    elif m[0].type == 'OP_HLT':
      self.assembler.hlt()
    else:
      raise ValueError(f'Unknown op: {m}')


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
      self.addr = None
      self.name = None
      self.fixups = []

  def write(self, instr):
    self.rom.rom[self.addr] = instr
    self.addr += 1

  def __enter__(self):
    return self

  def __exit__(self, a, b, c):
    for l in self.labels:
      if l.addr is None:
        raise ValueError(f'Undefined label "{l.name}"')
      for f in l.fixups:
        f()

  def label(self, l):
    if l.addr is not None:
      raise ValueError('Label redefinition')
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

  def alu_not(self, dst):
    self.alu(dst, 0)

  def alu_xor(self, dst):
    self.alu(dst, 1)

  def alu_or(self, dst):
    self.alu(dst, 2)

  def alu_and(self, dst):
    self.alu(dst, 3)

  def alu_add(self, dst):
    self.alu(dst, 4)

  def alu_sub(self, dst):
    self.alu(dst, 5)

  def alu_cmp(self):
    self.alu('a', 6)

  def alu_shl(self, dst):
    self.alu(dst, 7)

  def alu_shr(self, dst):
    self.alu(dst, 8)

  def alu_inc(self, dst):
    self.alu(dst, 9)

  def alu_dec(self, dst):
    self.alu(dst, 10)

  def alu_neg(self, dst):
    self.alu(dst, 11)

  def alu_clf(self):
    self.alu('a', 12)

  def alu_inv(self):
    self.alu('a', 13)

  def alu_rol(self, dst):
    self.alu(dst, 14)

  def alu_ror(self, dst):
    self.alu(dst, 15)

  def jmp(self, addr='c:d', t=0):
    addr = addr.lower()
    if addr not in Assembler.ADDR_REGISTERS:
      raise ValueError(f'Invalid jump register: {addr}.')
    self.write(Assembler.PREFIX_JMP | (Assembler.ADDR_REGISTERS.index(addr) << 3) | t)

  def jmp_jmp(self, addr):
    self.jmp(addr, 0)

  def jmp_jz(self, addr):
    self.jmp(addr, 1)

  def jmp_je(self, addr):
    self.jmp(addr, 1)

  def jmp_jnz(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 1)

  def jmp_jne(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 1)

  def jmp_jn(self, addr):
    self.jmp(addr, 2)

  def jmp_jp(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 2)

  def jmp_jls(self, addr):
    self.jmp(addr, 3)

  def jmp_jges(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 3)

  def jmp_jc(self, addr):
    self.jmp(addr, 4)

  def jmp_jlu(self, addr):
    self.jmp(addr, 4)

  def jmp_jnc(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 4)

  def jmp_jgeu(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 4)

  def jmp_jo(self, addr):
    self.jmp(addr, 5)

  def jmp_jno(self, addr):
    self.alu_inv('a')
    self.jmp(addr, 5)

  def rmem(self, dst='a', addr='c:d'):
    # 1110rrwa  r/w mem rr=A,B,E,F a=(C:D, G:H)
    dst = dst.lower()
    addr = addr.lower()
    if dst not in Assembler.MEM_REGISTERS:
      raise ValueError(f'Invalid mem dst register: {dst}.')
    if addr not in Assembler.ADDR_REGISTERS:
      raise ValueError(f'Invalid addr register: {addr}.')
    self.write(Assembler.PREFIX_MEM | (Assembler.MEM_REGISTERS.index(dst) << 2) | Assembler.MEM_READ | Assembler.ADDR_REGISTERS.index(addr))

  def wmem(self, addr='c:d', src='a'):
    src = src.lower()
    addr = addr.lower()
    if src not in Assembler.MEM_REGISTERS:
      raise ValueError(f'Invalid mem src register: {dst}.')
    if addr not in Assembler.ADDR_REGISTERS:
      raise ValueError(f'Invalid addr register: {addr}.')
    self.write(Assembler.PREFIX_MEM | (Assembler.MEM_REGISTERS.index(src) << 2) | Assembler.MEM_WRITE | Assembler.ADDR_REGISTERS.index(addr))

  def hlt(self):
    l = Assembler.Label()
    self.loadlabel('c:d', l)
    self.label(l)
    self.jmp('c:d')

  def parse(self, path):
    with open(path) as f:
      contents = f.read()
      try:
        ast = l.parse(contents)
      except UnexpectedInput as e:
        print(f'{path}:{e.line}:{e.column}: unexpected input.')
        print('  ' + contents.split('\n')[e.line-1])
        print('  ' + ' ' * e.column + '^')
        return False
      AssemblerTransformer(self).transform(ast)
      return True
