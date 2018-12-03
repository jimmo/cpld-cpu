import collections
from lark import Lark, UnexpectedInput

l = Lark(open('v2a/asm.g').read(), parser='earley', lexer='auto')

PAGE_SIZE = 0x1000

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
    print(' '.join(x.value for x in m))
    if m[0].type == 'CMD_ORG':
      self.assembler.org(self.parse_number(m[1]))
    elif m[0].type == 'CMD_PAGE':
      self.assembler.page(m[1], self.parse_number(m[2]))
    else:
      raise ValueError(f'Unknown command: {m}')
  
  def op(self, m):
    if m[0].type == 'LABEL':
      print(m[0] + ':')
      self.assembler.label(self.assembler.create_label(m[0]))
      m = m[1:]

    print(' '.join(x.value for x in m))
    if m[0].type == 'OP_DCB':
      self.assembler.dcb(self.parse_number(m[1]))
      return

    label = None
    if len(m) == 2 and m[0].type != 'OP_LDPG':
      if m[1].type == 'NUMBER':
        label = self.assembler.const(self.parse_number(m[1]))
      else:
        label = self.assembler.create_label(m[1])
    
    if m[0].type == 'OP_NOR':
      self.assembler.nor(label)
    elif m[0].type == 'OP_ADD':
      self.assembler.add(label)
    elif m[0].type == 'OP_STA':
      self.assembler.sta(label)
    elif m[0].type == 'OP_CLR':
      self.assembler.nor(self.assembler.create_label('allone'))
    elif m[0].type == 'OP_LDA':
      self.assembler.lda(label)
    elif m[0].type == 'OP_NOT':
      self.assembler.nor(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_SUB':
      self.assembler.nor(self.assembler.create_label('zero'))
      self.assembler.add(label)
      self.assembler.nor(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_NORX':
      self.assembler.norx(label)
    elif m[0].type == 'OP_ADDX':
      self.assembler.addx(label)
    elif m[0].type == 'OP_STX':
      self.assembler.stx(label)
    elif m[0].type == 'OP_CLRX':
      self.assembler.norx(self.assembler.create_label('allone'))
    elif m[0].type == 'OP_LDX':
      self.assembler.ldx(label)
    elif m[0].type == 'OP_NOTX':
      self.assembler.norx(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_SUBX':
      self.assembler.norx(self.assembler.create_label('zero'))
      self.assembler.addx(label)
      self.assembler.norx(self.assembler.create_label('zero'))
    elif m[0].type == 'OP_JCC':
      self.assembler.jcc(label)
    elif m[0].type == 'OP_JNZ':
      self.assembler.jnz(label)
    elif m[0].type == 'OP_JMP':
      self.assembler.jcc(label)
      self.assembler.jcc(label)
    elif m[0].type == 'OP_JCS':
      self.assembler.jcs(label)
    elif m[0].type == 'OP_JZ':
      self.assembler.jz(label)
    elif m[0].type == 'OP_LDPG':
      self.assembler.ldpg(m[1])
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
    self._pages = collections.defaultdict(Assembler.Page)
    self._labels = collections.defaultdict(Assembler.Label)
    self._indent = 0

  def log(self, s):
    print('  0x{:04x}: {}{}'.format(self._offset, '  ' * self._indent, s))

  def create_label(self, name):
    l = self._labels[name]
    l._name = name
    return l

  class Label:
    def __init__(self):
      self._offset = None
      self._page = None
      self._name = None
      self._fixups = []
      self._register = False

    def addr(self):
      return self._offset | (self._page._target << 12)

  class Page:
    def __init__(self):
      self._name = None
      self._num = None
      self._target = None
      self._nreserved = 0
      self._fixups = []
      self._consts = {}

    def linear(self, offset=0):
      return self._num * PAGE_SIZE + offset

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
    for p in self._pages.values():
      if p._num is None:
        raise ValueError(f'Undefined page "{p._name}"')
      self._page = p
      for name, offset_num, offset_sta in p._fixups:
        self.log('fixup: {}::{} --> 0x{:04x} 0x{:04x}'.format(p._name, name, offset_num, offset_sta))
        self._offset = offset_num
        self.dcb(self._pages[name]._num)
        self._offset = offset_sta
        self.sta(self.create_label('bank{}'.format(self._pages[name]._target)))

    for l in self._labels.values():
      if l._offset is None:
        raise ValueError(f'Undefined label "{l._name}"')
      for page, offset, is_jump in l._fixups:
        if is_jump:
          if page._target == l._page._target and page._num != l._page._num:
            raise ValueError(f'Same-target jump to {l._name}')
        else:
          if page._target == l._page._target and page._num != l._page._num and not l._register:
            raise ValueError(f'Referecing label {l._name} from a different page in the same bank')
        linear = page.linear(offset)
        addr = l.addr()
        self._data[linear] |= (addr >> 8) & 0x1f
        self._data[linear+1] |= addr & 0xff

  def org(self, addr):
    self._offset = addr

  def page(self, name, target):
    self._page = self._pages[name]
    if self._page._num is not None:
      raise ValueError('Redefinition of page')
    self._page._name = name
    self._page._num = len(self._pages) - 1
    self._page._target = target

    if target == 0:
      self.reserve('one', 1, register=True)
      self.reserve('allone', 0xff, register=True)
      self.reserve('zero', 0, register=True)
      self.reserve('trigger', 0, register=True)
      self.reserve('display', 0, register=True)
      self.reserve('bank1', 0, register=True)
      self.reserve('bank0', 0, register=True)
      self.reserve('_tmp1', 0, register=True)
      self.reserve('_tmp2', 0, register=True)
      self.reserve('_sp', 0, register=True)
      self.reserve('_stack', [0]*32, register=True)
    
    self._offset = 0

  def const(self, value):
    if value in self._page._consts:
      return self._page._consts[value]
    name = '_const_{}_{}'.format(self._page._num, value)
    l = self.create_label(name)
    self.reserve(name, value)
    self._page._consts[value] = l
    return l

  def reserve(self, name, value, register=False):
    if isinstance(value, int):
      value = [value]
    prev_offset = self._offset
    self._offset = PAGE_SIZE - len(value) - self._page._nreserved
    self._page._nreserved += len(value)
    self.label(self.create_label(name), register)
    offset = self._offset
    for x in value:
      self.dcb(x)
    self._offset = prev_offset
    return offset
        
  def label(self, l, register=False):
    self.log('  label "{}" at 0x{:04x}'.format(l._name, self._offset))
    if register and self._page._num != 0:
      return
    if l._offset is not None:
      raise ValueError(f'Label redefinition: {l._name}')
    l._page = self._page
    l._offset = self._offset
    l._register = register

  def placeholder(self, label, is_jump=False):
    label._fixups.append((self._page, self._offset, is_jump))

  def nor(self, label):
    self.log('  nor {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_NOR)
  
  def add(self, label):
    self.log('  add {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_ADD)
  
  def sta(self, label):
    self.log('  sta {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_STA)
  
  def lda(self, label):
    self.log('  lda {}'.format(label._name))
    self._indent += 1
    self.nor(self.create_label('allone'))
    self.add(label)
    self._indent -= 1
    
  def norx(self, label):
    self.log('  norx {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_NORX)
  
  def addx(self, label):
    self.log('  addx {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_ADDX)
  
  def stx(self, label):
    self.log('  stx {}'.format(label._name))
    self.placeholder(label)
    self.write_instr(Assembler.PREFIX_STX)
  
  def ldx(self, label):
    self.log('  ldx {}'.format(label._name))
    self._indent += 1
    self.norx(self.create_label('allone'))
    self.addx(label)
    self._indent -= 1

  def jcc(self, label):
    self.log('  jcc {}'.format(label._name))
    self.placeholder(label, is_jump=True)
    self.write_instr(Assembler.PREFIX_JCC)

  def jcs(self, label):
    self.log('  jcs {}'.format(label._name))
    self.write_instr(Assembler.PREFIX_JCC | (self._page._target << 12) | (self._offset + 4))
    self._indent += 1
    self.jcc(label)
    self._indent -= 1
  
  def jnz(self, label):
    self.log('  jnz {}'.format(label._name))
    self.placeholder(label, is_jump=True)
    self.write_instr(Assembler.PREFIX_JNZ)

  def jz(self, label):
    self.log('  jz {}'.format(label._name))
    self.write_instr(Assembler.PREFIX_JNZ | (self._page._target << 12) | (self._offset + 4))
    self._indent += 1
    self.jcc(label)
    self._indent -= 1

  def ldpg(self, name):
    self.log('  ldpg {}'.format(name))
    self._indent += 1
    label_name = '_page_{}_{}'.format(self._page._num, name)
    offset = self.reserve(label_name, 0)
    self.sta(self.create_label('_tmp1'))
    self.lda(self.create_label(label_name))
    self._page._fixups.append((name, offset, self._offset,))
    self.dcb(0)  # Replace with `sta bankN`
    self.dcb(0)
    self.lda(self.create_label('_tmp1'))
    self._indent -= 1
  
  def hlt(self):
    self.log('  hlt')
    self.write_instr(Assembler.PREFIX_JCC | (self._page._target << 12) | self._offset)
    self.write_instr(Assembler.PREFIX_JCC | (self._page._target << 12) | self._offset)

  def dcb(self, v):
    self.log('  dcb 0x{:02x}'.format(v))
    self.write_byte(v)

  def parse(self, path):
    with open(path) as f:
      contents = f.read()
      try:
        ast = l.parse(contents)
      except UnexpectedInput as e:
        self.log(f'{path}:{e.line}:{e.column}: unexpected input.')
        self.log('  ' + contents.split('\n')[e.line-1])
        self.log('  ' + ' ' * e.column + '^')
        return False
      AssemblerTransformer(self).transform(ast)
      return True
