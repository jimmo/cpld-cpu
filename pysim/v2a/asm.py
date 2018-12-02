import collections
from lark import Lark, UnexpectedInput

l = Lark(open('v2a/asm.g').read(), parser='earley', lexer='auto')

class AssemblerTransformer():
  def __init__(self, assembler):
    self.assembler = assembler

  def transform(self, ast):
    for statement in ast.children:
      if statement.data == 'statement':
        statement = statement.children[0]
        if statement.data == 'cmd':
          self.cmd(statement.children)
        elif statement.data == 'op':
          self.op(statement.children)
        else:
          raise ValueError('Unknown statment', statement)

  def parse_number(self, token):
    if token.type != 'NUMBER':
      raise ValueError(f'Invalid number token type {token.type} "{token}"')
    if token.startswith('0x'):
      return int(token, 16)
    if token.startswith('0o'):
      return int(token, 8)
    return int(token, 10)

  def cmd(self, m):
    if m[0].type == 'CMD_ORG':
      self.assembler.org(self.parse_number(m[1]))
    elif m[0].type == 'CMD_PAGE':
      self.assembler.page(m[1], self.parse_number(m[2]))
    else:
      raise ValueError(f'Unknown command: {m}')
  
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
  PREFIX_NOR =  0b00000000_00000000
  PREFIX_ADD =  0b00100000_00000000
  PREFIX_STA =  0b01000000_00000000
  PREFIX_JCC =  0b01100000_00000000
  PREFIX_NORX = 0b10000000_00000000
  PREFIX_ADDX = 0b10100000_00000000
  PREFIX_STX = 0b11000000_00000000
  PREFIX_JNZ =  0b11100000_00000000

  def __init__(self, data, addr):
    print(len(data))
    self._data = data
    self._offset = 0
    self._page = None
    self._pages = []
    self._labels = set()
    self._labels_by_name = collections.defaultdict(Assembler.Label)

  def create_label(self, name):
    l = self._labels_by_name[name]
    l._name = name
    self._labels.add(l)
    return l

  class Label:
    def __init__(self):
      self._offset = None
      self._page = None
      self._name = None
      self._fixups = []
      self._special = False

    def addr(self):
      return self._offset | (self._page._target << 12)

  class Page:
    def __init__(self):
      self._name = None
      self._num = None
      self._target = None

    def linear(self, offset=0):
      return self._num * 0x1000 + offset

  def write_instr(self, instr):
    self._data[self._page.linear(self._offset)] = instr >> 8
    self._data[self._page.linear(self._offset+1)] = instr & 0xff
    self._offset += 2

  def write_byte(self, b):
    self._data[self._page.linear(self._offset)] = b & 0xff
    self._offset += 1

  def __enter__(self):
    self.page('default', 0)
    return self

  def __exit__(self, a, b, c):
    for l in self._labels:
      print(l._name)
      if l._offset is None:
        raise ValueError(f'Undefined label "{l._name}"')
      for page, offset, is_jump in l._fixups:
        if is_jump:
          if page._target == l._page._target and page._num != l._page._num:
            raise ValueError(f'Same-target jump to {l._name}')
        else:
          if page._target == l._page._target and page._num != l._page._num and not l._special:
            raise ValueError(f'Referecing label {l._name} from a different page in the same bank')
        linear = page.linear(offset)
        addr = l.addr()
        self._data[linear] |= (addr >> 8) & 0x1f
        self._data[linear+1] |= addr & 0xff

  def org(self, addr):
    self._offset = addr

  def page(self, name, target):
    self._page = Assembler.Page()
    self._page._name = name
    self._page._num = len(self._pages)
    self._page._target = target
    self._pages.append(self._page)

    if target == 0:
      num_reserved = 2 + 2 + 3
      self._offset = 2**12 - num_reserved
      self.label(self.create_label('bank0'), True)
      self.dcb(0)
      self.label(self.create_label('bank1'), True)
      self.dcb(0)
      self.label(self.create_label('display'), True)
      self.dcb(0)
      self.label(self.create_label('trigger'), True)
      self.dcb(0)
      self.label(self.create_label('zero'), True)
      self.dcb(0)
      self.label(self.create_label('allone'), True)
      self.dcb(0xff)
      self.label(self.create_label('one'), True)
      self.dcb(1)
    
    self._offset = 0
        
  def label(self, l, special=False):
    if special and self._page._num != 0:
      return
    if l._offset is not None:
      raise ValueError(f'Label redefinition: {l._name}')
    l._page = self._page
    l._offset = self._offset
    l._special = special

  def placeholder(self, label, is_jump=False):
    self._labels.add(label)
    label._fixups.append((self._page, self._offset, is_jump))

  def nor(self, label):
    print('nor {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_NOR)
  
  def add(self, label):
    print('add {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_ADD)
  
  def sta(self, label):
    print('sta {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_STA)
  
  def lda(self, label):
    print('  lda {}'.format(label._name))
    self.nor(self.create_label('allone'))
    self.add(label)
    
  def norx(self, label):
    print('norx {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_NORX)
  
  def addx(self, label):
    print('addx {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_ADDX)
  
  def stx(self, label):
    print('stx {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_STX)
  
  def ldx(self, label):
    print('  ldx {}'.format(label._name))
    self.norx(self.create_label('allone'))
    self.addx(label)

  def jcc(self, label):
    print('jcc {}'.format(label._name))
    self.placeholder(label, is_jump=True)
    self.write_instr(Assembler.PREFIX_JCC)

  def jcs(self, label):
    print('  jcs {}'.format(label._name))
    self.write_instr(Assembler.PREFIX_JCC | (self._page._target << 12) | (self._offset + 4))
    self.jcc(label)
  
  def jnz(self, label):
    print('jnz {}'.format(label._name))
    self.placeholder(label, is_jump=True)
    self.write_instr(Assembler.PREFIX_JNZ)

  def jz(self, label):
    print('  jz {}'.format(label._name))
    self.write_instr(Assembler.PREFIX_JNZ | (self._page._target << 12) | (self._offset + 4))
    self.jcc(label)
  
  def hlt(self):
    print('  hlt')
    self.write_instr(Assembler.PREFIX_JCC | (self._page._target << 12) | self._offset)
    self.write_instr(Assembler.PREFIX_JCC | (self._page._target << 12) | self._offset)

  def dcb(self, v):
    print('dcb 0x{:02x} (at 0x{:02x})'.format(v, self._offset))
    self.write_byte(v)

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
