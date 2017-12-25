import collections
import sys

from lark import Lark, Transformer, Tree
from lark.lexer import UnexpectedInput

from asm import Assembler

l = Lark(open('zz.g').read())


class Variable():
  def __init__(self, name, addr, typename):
    self.name = name
    self.addr = addr
    self.signed = typename[0] == 'i'
    self.size = 1 if typename[1:] == '8' else 2

  def desc(self):
    return ('' if self.signed else 'u') + 'int' + str(self.size * 8) + ' ' + self.name


class CompilerTransformer(Transformer):
  def __init__(self):
    self.vars = {}
    self.next_var = 0
    self.call_n = 0

    # Init call stack pointer.
    print(f'  load c:d, 0xffef')
    print(f'  load a, 0')
    print(f'  wmem c:d, a')


  def var(self, n):
    if n not in self.vars:
      raise ValueError(f'Unknown variable "{n}".')
    return self.vars[n]

  def format_expr(self, expr):
    if isinstance(expr, Tree):
      if expr.data == 'bin_op':
        return '(' + self.format_expr(expr.children[0]) + expr.children[1] + self.format_expr(expr.children[2]) + ')'
      raise ValueError(f'unknown expr type {expr.data}')
    else:
      if expr.type == 'NUMBER':
        return expr
      elif expr.type == 'ID':
        v = self.var(expr)
        return v.name
      else:
        raise ValueError(f'unknown token type {expr.type}')

  ALU_OPS = {
    '+': 'add',
    '-': 'sub',
    '&': 'and',
    '|': 'or',
    '^': 'xor',
  }

  def number(self, token):
    if token.type != 'NUMBER':
      raise ValueError(f'Invalid number token type {token.type} "{token}"')
    if token.startswith('0x'):
      return int(token, 16)
    if token.startswith('0o'):
      return int(token, 8)
    return int(token, 10)

  def eval(self, expr, n=0):
    if isinstance(expr, Tree):
      if expr.data == 'bin_op':
        self.eval(expr.children[2])
        print(f'  # save {self.format_expr(expr.children[2])}')
        print(f'  load c:d, 0x{0xffff-n:04x}')
        print(f'  wmem c:d, a')

        self.eval(expr.children[0], n+1)

        print(f'  # restore {self.format_expr(expr.children[2])}')
        print(f'  load c:d, 0x{0xffff-n:04x}')
        print(f'  rmem b, c:d')

        op = CompilerTransformer.ALU_OPS[expr.children[1]]
        print(f'  # {expr.children[1]}')
        print(f'  {op} a')
      else:
        raise ValueError(f'unknown expr type {expr.data}')
    else:
      if expr.type == 'NUMBER':
        print(f'  # {expr}')
        v = self.number(expr)
        print(f'  load a, 0x{v:x}')
      elif expr.type == 'ID':
        v = self.var(expr)
        if v.size != 1:
          raise ValueError('Must be 8-bit variable')
        print(f'  # {v.name}')
        print(f'  load c:d, 0x{v.addr:04x}')
        print(f'  rmem a, c:d')
      else:
        raise ValueError(f'unknown token type {expr.type}')

  def eval16(self, expr, n=0):
    if isinstance(expr, Tree):
      if expr.data == 'bin_op':
        self.eval16(expr.children[2])

        # TODO
        print(f'  mov a, b')

        print(f'  # save {self.format_expr(expr.children[2])}')
        print(f'  load c:d, 0x{0xffff-n:04x}')
        print(f'  wmem c:d, a')

        self.eval16(expr.children[0], n+1)

        # TODO
        print(f'  mov a, b')

        print(f'  # restore {self.format_expr(expr.children[2])}')
        print(f'  load c:d, 0x{0xffff-n:04x}')
        print(f'  rmem b, c:d')

        op = CompilerTransformer.ALU_OPS[expr.children[1]]
        print(f'  # {expr.children[1]}')
        print(f'  {op} a')

        # TODO
        print(f'  mov b, a')
        print(f'  load a, 0')
      else:
        raise ValueError(f'unknown expr type {expr.data}')
    else:
      if expr.type == 'NUMBER':
        print(f'  # {expr} (16-bit)')
        v = self.number(expr)
        print(f'  load a:b, 0x{v:x}')
      elif expr.type == 'ID':
        v = self.var(expr)
        if v.size != 2:
          raise ValueError('Must be 16-bit variable')
        print(f'  # {v.name} (16-bit)')
        print(f'  load c:d, 0x{v.addr:04x}')
        print(f'  rmem a, c:d')
        print(f'  mov b, a')
        print(f'  mov a, d')
        print(f'  inc a')
        print(f'  mov d, a')
        print(f'  rmem b, c:d')
      else:
        raise ValueError(f'unknown token type {expr.type}')

  def new_assign(self, m):
    if m[1] in self.vars:
      raise ValueError(f'Redefinition of {m[1]}')
    v = Variable(m[1], self.next_var, m[0])
    self.vars[m[1]] = v
    self.next_var += v.size
    self.assign(m[1:])

  def assign(self, m):
    v = self.var(m[0])
    print(f'  # {v.name} = {self.format_expr(m[1])}')
    if v.size == 1:
      self.eval(m[1])
      print(f'  load c:d, 0x{v.addr:04x}')
      print(f'  wmem c:d, a')
    elif v.size == 2:
      self.eval16(m[1])
      print(f'  load c:d, 0x{v.addr:04x}')
      print(f'  wmem c:d, a')
      print(f'  mov a, d')
      print(f'  inc a')
      print(f'  mov d, a')
      print(f'  wmem c:d, b')
    else:
      raise ValueError('Only 8- and 16- bit values supported.')
    print()

  def deref_assign(self, m):
    v = self.var(m[0][1:-1])
    if v.size != 2 or v.signed:
      raise ValueError(f'Can only dereference u16 type variables ({v.desc()}).')
    print(f'  # [{v.name}] = {self.format_expr(m[1])}')
    print(f'  load c:d, 0x{v.addr:04x}')
    print('  rmem e, c:d')
    print('  mov a, d')
    print('  inc a')
    print('  mov d, a')
    print('  rmem f, c:d')
    print('  mov g:h, e:f')
    self.eval(m[1])
    print('  wmem g:h, a')
    print()

  def hlt(self, m):
    print('  hlt')
    print()

  JUMP_TYPES = {
    '==': 'je',
    '!=': 'jne',
    '>': 'jxx',
    '<': 'jn',
    '>=': 'jp',
    '<=': 'jxx',
  }

  def goto(self, m):
    if len(m) == 1:
      print(f'  # goto {m[0]}')
      print(f'  load c:d, {m[0]}')
      print(f'  jmp c:d')
    else:
      print(f'  # if {m[0]} {m[1]} {m[2]} goto {m[3]}')
      self.eval(m[2])
      print('  mov g, a')
      self.eval(m[0])
      print('  mov b, g')
      print('  cmp')
      print(f'  load c:d, {m[3]}')
      jmp = CompilerTransformer.JUMP_TYPES[m[1]]
      print(f'  {jmp} c:d')
    print()

  def label(self, m):
    print(m[0] + ':')

  def call(self, m):
    n = f'_call_{self.call_n}'
    self.call_n += 1

    print(f'  # call {m[0]}')

    # Point c:d at the next location
    print(f'  load c:d, 0xffef')
    print(f'  rmem b, c:d')
    print(f'  load a, 0xed')
    print(f'  sub a')
    print(f'  mov d, a')

    # Stash this label in c:d
    print(f'  load a:b, {n}')
    print(f'  wmem c:d, a')
    print(f'  mov a, d')
    print(f'  inc a')
    print(f'  mov d, a')
    print(f'  wmem c:d, b')

    # Update stack pointer
    print(f'  load c:d, 0xffef')
    print(f'  rmem a, c:d')
    print(f'  load b, 2')
    print(f'  add a')
    print(f'  wmem c:d, a')

    # Jump to call target
    print(f'  load c:d, {m[0]}')
    print(f'  jmp c:d')
    print(f'{n}:')
    print()

  def ret(self, m):
    print(f'  # ret')

    # Point c:d at the current location
    print(f'  load c:d, 0xffef')
    print(f'  rmem b, c:d')
    print(f'  load a, 0xef')
    print(f'  sub a')
    print(f'  mov d, a')

    # Get return target
    print(f'  rmem b, c:d')
    print(f'  mov a, d')
    print(f'  inc a')
    print(f'  mov d, a')
    print(f'  mov a, b')
    print(f'  rmem b, c:d')
    print(f'  mov g:h, a:b')

    # Update stack pointer
    print(f'  load c:d, 0xffef')
    print(f'  rmem a, c:d')
    print(f'  load b, 2')
    print(f'  sub a')
    print(f'  wmem c:d, a')

    # Jump to target
    print(f'  jmp g:h')
    print()


class Compiler():
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
      CompilerTransformer().transform(ast)
      return True

Compiler().parse(sys.argv[1])
