import collections
from lark import Lark, UnexpectedInput

l = Lark(open('v2a/asm.g').read(), parser='earley', lexer='auto')

class AssemblerTransformer():
  def __init__(self, assembler):
    self.assembler = assembler

  def transform(self, ast):
    for op in ast.children:
      self.op(op.children)

  def parse_number(self, token):
    if token.type != 'NUMBER':
      raise ValueError(f'Invalid number token type {token.type} "{token}"')
    if token.startswith('0x'):
      return int(token, 16)
    if token.startswith('0o'):
      return int(token, 8)
    return int(token, 10)

  def op(self, m):
    if m[0].type == 'LABEL':
      self.assembler.label(self.assembler.create_label(m[0]))
      m = m[1:]

    if m[0].type == 'OP_DCB':
      self.assembler.dcb(self.parse_number(m[1]))
    elif m[0].type == 'OP_NOR':
      self.assembler.nor(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_ADD':
      self.assembler.add(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_STA':
      self.assembler.sta(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_CLR':
      self.assembler.nor(self.assembler.create_label('allone'))
    elif m[0].type == 'OP_LDA':
      self.assembler.lda(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_NOT':
      self.assembler.nor(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_SUB':
      self.assembler.nor(self.assembler.create_label('zero'))
      self.assembler.add(self.assembler.create_label(m[1]))
      self.assembler.nor(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_NORX':
      self.assembler.norx(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_ADDX':
      self.assembler.addx(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_STX':
      self.assembler.stx(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_CLRX':
      self.assembler.norx(self.assembler.create_label('allone'))
    elif m[0].type == 'OP_LDX':
      self.assembler.ldx(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_NOTX':
      self.assembler.norx(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_SUBX':
      self.assembler.norx(self.assembler.create_label('zero'))
      self.assembler.addx(self.assembler.create_label(m[1]))
      self.assembler.norx(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_JCC':
      self.assembler.jcc(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_JNZ':
      self.assembler.jnz(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_JMP':
      self.assembler.jcc(self.assembler.create_label(m[1]))
      self.assembler.jcc(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_JCS':
      self.assembler.jcs(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_JZ':
      self.assembler.jz(self.assembler.create_label(m[1]))
    elif m[0].type == 'OP_HLT':
      self.assembler.hlt()
    elif m[0].type == 'OP_OUT':
      self.assembler.sta(self.assembler.create_label('display'))
      self.assembler.lda(self.assembler.create_label('trigger'))
      self.assembler.nor(self.assembler.create_label('one'))
      self.assembler.sta(self.assembler.create_label('trigger'))
      self.assembler.lda(self.assembler.create_label('display'))
    else:
      raise ValueError(f'Unknown op: {m}')

class Assembler:
  PREFIX_NOR =  0b00000000
  PREFIX_ADD =  0b00100000
  PREFIX_STA =  0b01000000
  PREFIX_JCC =  0b01100000
  PREFIX_NORX = 0b10000000
  PREFIX_ADDX = 0b10100000
  PREFIX_STX = 0b11000000
  PREFIX_JNZ =  0b11100000

  def __init__(self, data, addr):
    print(len(data))
    self.data = data
    self.addr = addr
    self.labels = set()
    self.labels_by_name = collections.defaultdict(Assembler.Label)

  def create_label(self, name):
    l = self.labels_by_name[name]
    l.name = name
    self.labels.add(l)
    return l

  class Label:
    def __init__(self):
      self.addr = None
      self.name = None
      self.fixups = []

  def write(self, instr):
    self.data[self.addr] = instr
    self.addr += 1

  def __enter__(self):
    return self

  def __exit__(self, a, b, c):
    self.addr = 2**5 - 5
    self.label(self.create_label('display'))
    self.dcb(0)
    self.label(self.create_label('trigger'))
    self.dcb(0)
    self.label(self.create_label('zero'))
    self.dcb(0)
    self.label(self.create_label('allone'))
    self.dcb(0xff)
    self.label(self.create_label('one'))
    self.dcb(1)
    
    for l in self.labels:
      if l.addr is None:
        raise ValueError(f'Undefined label "{l.name}"')
      for f in l.fixups:
        self.data[f] |= l.addr

  def label(self, l):
    if l.addr is not None:
      raise ValueError('Label redefinition')
    l.addr = self.addr

  def placeholder(self, label):
    self.labels.add(label)
    label.fixups.append(self.addr)

  def nor(self, label):
    print('nor {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_NOR)
  
  def add(self, label):
    print('add {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_ADD)
  
  def sta(self, label):
    print('sta {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_STA)
  
  def lda(self, label):
    print('  lda {}'.format(label.name))
    self.nor(self.create_label('allone'))
    self.add(label)
    
  def norx(self, label):
    print('norx {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_NORX)
  
  def addx(self, label):
    print('addx {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_ADDX)
  
  def stx(self, label):
    print('stx {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_STX)
  
  def ldx(self, label):
    print('  ldx {}'.format(label.name))
    self.norx(self.create_label('allone'))
    self.addx(label)

  def jcc(self, label):
    print('jcc {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_JCC)

  def jcs(self, label):
    print('  jcs {}'.format(label.name))
    self.write(Assembler.PREFIX_JCC | (self.addr + 2))
    self.jcc(label)
  
  def jnz(self, label):
    print('jnz {}'.format(label.name))
    self.placeholder(label)
    self.write(Assembler.PREFIX_JNZ)

  def jz(self, label):
    print('  jz {}'.format(label.name))
    self.write(Assembler.PREFIX_JNZ | (self.addr + 2))
    self.jnz(label)
  
  def hlt(self):
    print('  hlt')
    self.write(Assembler.PREFIX_JCC | self.addr)
    self.write(Assembler.PREFIX_JCC | self.addr)

  def dcb(self, v):
    print('dcb 0x{:02x} (at 0x{:02x})'.format(v, self.addr))
    self.write(v)

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
