import sys

DEPTH = 0

def depth(n):
  global DEPTH
  DEPTH += n

def debug(msg):
  print('  '*DEPTH + msg)
  if DEPTH > 400:
    print('Depth limit exceeded')
    sys.exit(1)

# Represents either a pin (or set of pins) on a component.
# Multiple signals are joined together in a Net.
class Signal:
  def __init__(self, p, w):
    # Parent component.
    self.parent = p
    # Width of this signal (i.e. number of bits).
    self.w = w
    # Current value (0..2^w-1).
    self.v = 0
    # Net that this signal is connected to.
    self.net = None
    # True if this signal is not currently driving the net.
    self.hiz = True
    # TODO
    self.edge = None

  def name(self):
    for n, s in self.parent.__dict__.items():
      if s == self:
        return n
    return 'unknown'

  # Called by the parent component (usually in update()) to either
  # drive the pin (v = 0 or 1) or set it to hi-z mode ( v= None).
  # All other singals on this net will be updated.
  def drive(self, v):
    depth(1)
    if v is not None and (v < 0 or v >= 2**self.w):
      print('Driving "{}/{}/{}" to "{}" invalid value.'.format(self.net.name, self.parent.name, self.name(), v))
    #debug('driving "{}/{}/{}" to "{}" (was "{}/{}")'.format(self.net.name, self.parent.name, self.name(), v, 'hiz' if self.hiz else 'loz', self.v))
    # Do nothing for no-op changes.
    if v is None:
      if not self.hiz:
        #debug('hiz mode')
        self.hiz = True
        self.net.update()
      #else:
      #  debug('ignore (same-hiz)')
    else:
      if self.v != v or self.hiz:
        #debug('driving mode')
        self.hiz = False
        self.v = v
        if self.net:
          self.net.update()
      #else:
      #  debug('ignore (same-v)')
    depth(-1)

  # Called by the net that this signal is connected to when another signal changes.
  def follow(self):
    depth(1)
    v = self.net.value()
    if v and not self.v:
      self.edge = 1
    if not v and self.v:
      self.edge = 0
    self.v = v
    #debug('following "{}/{}/{}" to "{}"'.format(self.net.name, self.parent.name, self.name(), v))
    if not self.hiz:
      debug('tried to follow a loz signal')
    self.parent.update()
    depth(-1)

  # Returns true if this signal had an edge since the last call.
  def was_edge(self, e):
    r = self.edge == e
    self.edge = None
    return r

  def value(self):
    if self.hiz:
      return self.net.value()
    else:
      return self.v

# Represents a set of connected signals.
class Net:
  def __init__(self, name, *signals):
    self.name = name

    # Check that all signals on this net are the same width.
    w_min, w_max = min(s.w for s in signals), max(s.w for s in signals)
    if w_min != w_max:
      debug('Mismatched signal widths on "{}".'.format(self.name))
      return

    self.w = w_min
    self.signals = signals

    # Ensure that all signals are not already on a net, and connect
    # them to this net.
    for s in self.signals:
      if s.net:
        debug('Already connected to net (trying to connect to "{}").'.format(self.name))
      s.net = self

  def value(self):
    # Find the current driver.
    driver = None
    for s in self.signals:
      if not s.hiz:
        if driver is not None:
          debug('Two drivers on net "{}"'.format(self.name))
          depth(-1)
          return
        driver = s
        break
    if driver:
      return driver.value()
    else:
      return 0

  # Called by a signal to update other signals in this net.
  def update(self):
    depth(1)
    #debug('updating net "{}"'.format(self.name))
    # Find the current driver.
    driver = None
    for s in self.signals:
      if s.hiz:
        s.follow()
    depth(-1)

# Base class for all components.
class Component:
  def __init__(self, n):
    self.name = n

class Logic(Component):
  def __init__(self):
    super().__init__('logic')
    self.in_a = Signal(self, 8)
    self.in_b = Signal(self, 8)
    self.fn = Signal(self, 4)
    self.out = Signal(self, 8)
    self.flags = Signal(self, 4)
    self.oe = Signal(self, 1)

  def update(self):
    pass

class Register(Component):
  def __init__(self, n):
    super().__init__('reg ' + n)
    self.v = 0
    self.data = Signal(self, 8)
    self.ie_l = Signal(self, 1)
    self.ie_h = Signal(self, 1)
    self.oe = Signal(self, 1)

  def update(self):
    depth(1)
    #debug('updating register')
    if self.ie_l.v:
      self.v = self.v & 0xf0 | self.data.v & 0x0f
    if self.ie_h.v:
      self.v = self.data.v & 0xf0 | self.v & 0x0f
    if self.oe.v:
      self.data.drive(self.v)
    else:
      self.data.drive(None)
    depth(-1)

class BusConnect(Component):
  def __init__(self, n):
    super().__init__('bus conn ' + n)
    self.a = Signal(self, 8)
    self.b = Signal(self, 8)
    self.a_to_b = Signal(self, 1)
    self.b_to_a = Signal(self, 1)

  def update(self):
    if self.a_to_b.v:
      self.b.drive(self.a.v)
    else:
      self.b.drive(None)
    if self.b_to_a.v:
      self.a.drive(self.b.v)
    else:
      self.a.drive(None)

class DecoderA(Component):
  def __init__(self):
    super().__init__('decoder a')
    self.instr = Signal(self, 8)
    self.clk = Signal(self, 2)
    self.skip = Signal(self, 1)
    self.a_to_b = Signal(self, 1)
    self.b_to_a = Signal(self, 1)
    self.a_to_t = Signal(self, 1)
    self.t_to_a = Signal(self, 1)
    self.ie_a_l = Signal(self, 1)
    self.ie_b_l = Signal(self, 1)
    self.ie_c_l = Signal(self, 1)
    self.ie_d_l = Signal(self, 1)
    self.ie_a_h = Signal(self, 1)
    self.ie_b_h = Signal(self, 1)
    self.ie_c_h = Signal(self, 1)
    self.ie_d_h = Signal(self, 1)
    self.ie_e = Signal(self, 1)
    self.ie_f = Signal(self, 1)
    self.ie_g = Signal(self, 1)
    self.ie_h = Signal(self, 1)
    self.ie_pc = Signal(self, 1)
    self.pc_inc = Signal(self, 1)
    self.logic_fn = Signal(self, 4)
    self.skip_mode = Signal(self, 4)

    self.outputs = [self.a_to_b, self.b_to_a, self.a_to_t, self.t_to_a, self.ie_a_l, self.ie_b_l, self.ie_c_l, self.ie_d_l, self.ie_a_h, self.ie_b_h, self.ie_c_h, self.ie_d_h, self.ie_e, self.ie_f, self.ie_g, self.ie_h, self.ie_pc, self.pc_inc]

  def stage(self, n, *high):
    if n != self.clk.v:
      return
    for s in self.outputs:
      if not self.skip.v and s in high:
        s.drive(1)
      else:
        s.drive(0)

  # 0xxx xndd load imm (n=high/low) (dd=A/B/C/D) (xxxx=data)
  # 10ss sddd copy register sss to ddd  (rrr=A/B/C/D/E/F/G/H)
  # 110f ffdf ALU (d=A/C) (ffff=function)
  # 1110 tttt skip (tttt=type)
  # 1111 0wtt read/write mem (w=read/write) (tt=type)
  # 1111 1?rr unconditional jump (rr=A:B/C:D/E:F/G:H) (?=type?)
  def update(self):
    if self.instr.v & (1<<7):
      if self.instr.v & (1<<6):
        pass
      else:
        pass
    else:
      # Load immediate
      self.stage(0)
      self.stage(1)
      self.stage(2, self.a_to_b)
      self.stage(3, self.pc_inc, self.a_to_b, [self.ie_a_l, self.ie_b_l, self.ie_c_l, self.ie_d_l][self.instr.v & 3])


class DecoderB(Component):
  def __init__(self):
    super().__init__('decoder b')
    self.instr = Signal(self, 8)
    self.clk = Signal(self, 2)
    self.skip = Signal(self, 1)
    self.oe_a = Signal(self, 1)
    self.oe_b = Signal(self, 1)
    self.oe_c = Signal(self, 1)
    self.oe_d = Signal(self, 1)
    self.oe_e = Signal(self, 1)
    self.oe_f = Signal(self, 1)
    self.oe_g = Signal(self, 1)
    self.oe_h = Signal(self, 1)
    self.ie_t = Signal(self, 1)
    self.oe_t = Signal(self, 1)
    self.ie_mem = Signal(self, 1)
    self.oe_mem = Signal(self, 1)
    self.oe_alu = Signal(self, 1)
    self.ie_ir = Signal(self, 1)
    self.oe_imm = Signal(self, 1)
    self.oe_skip = Signal(self, 1)
    self.ie_skip = Signal(self, 1)

    self.outputs = [self.oe_a, self.oe_b, self.oe_c, self.oe_d, self.oe_e, self.oe_f, self.oe_g, self.oe_h, self.ie_t, self.oe_t, self.ie_mem, self.oe_mem, self.oe_alu, self.ie_ir, self.oe_imm, self.oe_skip, self.ie_skip,]

  def stage(self, n, *high):
    if n != self.clk.v:
      return
    if n == 0:
      high = (*high, self.ie_ir)
    if n == 3:
      high = (*high, self.ie_skip)

    for s in self.outputs:
      if not self.skip.v and s in high:
        s.drive(1)
      else:
        s.drive(0)

  # 0xxx xndd load imm (n=high/low) (dd=A/B/C/D) (xxxx=data)
  # 10ss sddd copy register sss to ddd  (rrr=A/B/C/D/E/F/G/H)
  # 110f ffdf ALU (d=A/C) (ffff=function)
  # 1110 tttt skip (tttt=type)
  # 1111 0wtt read/write mem (w=read/write) (tt=type)
  # 1111 1?rr unconditional jump (rr=A:B/C:D/E:F/G:H) (?=type?)
  def update(self):
    if self.instr.v & (1<<7):
      pass
    else:
      # Load immediate
      self.stage(0)
      self.stage(1)
      self.stage(2, self.oe_imm)
      self.stage(3, self.oe_imm)

class InstructionRegister(Component):
  def __init__(self):
    super().__init__('ir')
    self.v = 0
    self.data = Signal(self, 8)
    self.instr = Signal(self, 8)
    self.imm = Signal(self, 8) # 2x
    self.ie = Signal(self, 1)
    self.oe_imm = Signal(self, 1)

  def update(self):
    if self.ie.v:
      self.v = self.data.v
      self.instr.drive(self.v)
    if self.oe_imm.v:
      self.imm.drive(0)
    else:
      self.imm.drive(None)

class ProgramCounter(Component):
  def __init__(self, n):
    super().__init__('pc ' + n)
    self.v = 0
    self.addr = Signal(self, 8)
    self.data = Signal(self, 8)
    self.rst = Signal(self, 1)
    self.inc = Signal(self, 1)
    self.ie = Signal(self, 1)
    self.co = Signal(self, 1)

  def update(self):
    if self.rst.v == 1:
      self.v = 0
    elif self.ie.v:
      self.v = self.data.v
    elif self.inc.was_edge(1):
      if self.v == 0xff:
        self.v = 0
        self.co.drive(1)
      else:
        self.v += 1
        self.co.drive(0)
    self.addr.drive(self.v)

class BranchFlags(Component):
  def __init__(self):
    super().__init__('branch flags')
    self.oe_skip = Signal(self, 1)
    self.flags = Signal(self, 4)
    self.mode = Signal(self, 4)
    self.ie_skip = Signal(self, 1)
    self.skip = Signal(self, 1)

  def update(self):
    pass

class IoPort(Component):
  def __init__(self):
    super().__init__('io port')
    self.mode = Signal(self, 1)
    self.ie = Signal(self, 1)
    self.oe = Signal(self, 1)
    self.data = Signal(self, 8)
    self.inp = Signal(self, 8)
    self.out = Signal(self, 8)

  def update(self):
    pass

class MemControl(Component):
  def __init__(self):
    super().__init__('mem ctrl')
    self.addr_l = Signal(self, 8)
    self.addr_h = Signal(self, 8)
    self.ie = Signal(self, 1)
    self.oe = Signal(self, 1)
    self.ie_ram = Signal(self, 1)
    self.ie_video = Signal(self, 1)
    self.ie_io = Signal(self, 1)
    self.oe_ram = Signal(self, 1)
    self.oe_io = Signal(self, 1)
    self.io_mode = Signal(self, 1)

  def update(self):
    self.io_mode.drive(self.addr_l.v & 1)
    if self.ie.v:
      if self.addr_h.v == 0 and self.addr_l.v < 2:
        self.ie_io.drive(1)
        self.ie_ram.drive(0)
      else:
        self.ie_io.drive(0)
        self.ie_ram.drive(1)
    else:
      self.ie_io.drive(0)
      self.ie_ram.drive(0)

    if self.oe.v:
      if self.addr_h.v == 0 and self.addr_l.v < 2:
        self.oe_io.drive(1)
        self.oe_ram.drive(0)
      else:
        self.oe_io.drive(0)
        self.oe_ram.drive(1)
    else:
      self.oe_io.drive(0)
      self.oe_ram.drive(0)

class Rom(Component):
  def __init__(self):
    super().__init__('rom')
    self.rom = list(range(65536))
    self.addr_l = Signal(self, 8)
    self.addr_h = Signal(self, 8)
    self.data = Signal(self, 8)

  def update(self):
    addr = self.addr_h.v << 8 | self.addr_l.v
    if addr < len(self.rom):
      self.data.drive(self.rom[addr])
    else:
      self.data.drive(0)

class Ram(Component):
  def __init__(self):
    super().__init__('ram')
    self.ram = [0] * 65536
    self.addr_l = Signal(self, 8)
    self.addr_h = Signal(self, 8)
    self.data = Signal(self, 8)
    self.ie = Signal(self, 1)
    self.oe = Signal(self, 1)

  def update(self):
    addr = self.addr_h.v << 8 | self.addr_l.v

    if self.ie.v:
      self.ram[addr] = self.data.v

    if self.oe.v:
      self.data.drive(self.ram[addr])
    else:
      self.data.drive(None)

class Clock(Component):
  def __init__(self):
    super().__init__('clock')
    self.clk = Signal(self, 2)

  def tick(self):
    debug('tick')
    self.clk.drive((self.clk.v + 1) % 4)

  def update(self):
    pass

def main():
  logic = Logic()
  reg_a = Register('a')
  reg_b = Register('b')
  reg_c = Register('c')
  reg_d = Register('d')
  reg_e = Register('e')
  reg_f = Register('f')
  reg_g = Register('g')
  reg_h = Register('h')
  reg_t = Register('t')
  bus_a_b = BusConnect('ab')
  bus_a_t = BusConnect('at')
  decoder_a = DecoderA()
  decoder_b = DecoderB()
  ir = InstructionRegister()
  pc_l = ProgramCounter('l')
  pc_h = ProgramCounter('h')
  branch_flags = BranchFlags()
  io = IoPort()
  mc = MemControl()
  ram = Ram()
  rom = Rom()
  clk = Clock()

  components = [logic, reg_a, reg_b, reg_c, reg_d, reg_e, reg_f, reg_g, reg_h, bus_a_b, bus_a_t, decoder_a, decoder_b, ir, pc_l, pc_h, branch_flags, io, mc, ram, rom, clk]

  # Register buses
  Net('bus a', reg_a.data, reg_c.data, reg_e.data, reg_g.data, logic.in_a, pc_l.data, ir.imm, mc.addr_l, ram.addr_l, bus_a_b.a, bus_a_t.a)
  Net('bus b', reg_b.data, reg_d.data, reg_f.data, reg_h.data, logic.in_b, pc_h.data, mc.addr_h, ram.addr_h, bus_a_b.b)
  Net('bus t', logic.out, ram.data, io.data, reg_t.data, bus_a_t.b)

  # Clock signals
  Net('clk', decoder_a.clk, decoder_b.clk, clk.clk)

  # Decoder inputs
  Net('instr', decoder_a.instr, decoder_b.instr, ir.instr)
  Net('skip', decoder_a.skip, decoder_b.skip, branch_flags.skip)

  # Decoder outputs
  Net('a to b', bus_a_b.a_to_b, decoder_a.a_to_b)
  Net('b to a', bus_a_b.b_to_a, decoder_a.b_to_a)
  Net('a to t', bus_a_t.a_to_b, decoder_a.a_to_t)
  Net('t to a', bus_a_t.b_to_a, decoder_a.t_to_a)
  Net('ie a l', reg_a.ie_l, decoder_a.ie_a_l)
  Net('ie a h', reg_a.ie_h, decoder_a.ie_a_h)
  Net('ie b l', reg_b.ie_l, decoder_a.ie_b_l)
  Net('ie b h', reg_b.ie_h, decoder_a.ie_b_h)
  Net('ie c l', reg_c.ie_l, decoder_a.ie_c_l)
  Net('ie c h', reg_c.ie_h, decoder_a.ie_c_h)
  Net('ie d l', reg_d.ie_l, decoder_a.ie_d_l)
  Net('ie d h', reg_d.ie_h, decoder_a.ie_d_h)
  Net('ie e', reg_e.ie_l, reg_e.ie_h, decoder_a.ie_e)
  Net('ie f', reg_f.ie_l, reg_f.ie_h, decoder_a.ie_f)
  Net('ie g', reg_g.ie_l, reg_g.ie_h, decoder_a.ie_g)
  Net('ie h', reg_h.ie_l, reg_h.ie_h, decoder_a.ie_h)

  Net('ie ir', ir.ie, decoder_b.ie_ir)
  Net('ie mc', mc.ie, decoder_b.ie_mem)
  Net('ie skip', branch_flags.ie_skip, decoder_b.ie_skip)
  Net('ie t', reg_t.ie_l, reg_t.ie_h, decoder_b.ie_t)

  Net('oe a', reg_a.oe, decoder_b.oe_a)
  Net('oe b', reg_b.oe, decoder_b.oe_b)
  Net('oe c', reg_c.oe, decoder_b.oe_c)
  Net('oe d', reg_d.oe, decoder_b.oe_d)
  Net('oe e', reg_e.oe, decoder_b.oe_e)
  Net('oe f', reg_f.oe, decoder_b.oe_f)
  Net('oe g', reg_g.oe, decoder_b.oe_g)
  Net('oe h', reg_h.oe, decoder_b.oe_h)
  Net('oe t', reg_t.oe, decoder_b.oe_t)
  Net('oe mc', mc.oe, decoder_b.oe_mem)
  Net('oe alu', logic.oe, decoder_b.oe_alu)
  Net('oe skip', branch_flags.oe_skip, decoder_b.oe_skip)
  Net('oe imm', ir.oe_imm, decoder_b.oe_imm)

  # Logic outputs
  Net('flags', logic.flags, branch_flags.flags)
  Net('logic fn', logic.fn, decoder_a.logic_fn)
  Net('skip fn', branch_flags.mode, decoder_a.skip_mode)

  # Instruction
  Net('rom addr l', rom.addr_l, pc_l.addr)
  Net('rom addr h', rom.addr_h, pc_h.addr)
  Net('rom data', rom.data, ir.data)

  # Program counter
  Net('pc carry', pc_l.co, pc_h.inc)
  Net('pc jmp', pc_l.ie, pc_h.ie, decoder_a.ie_pc)
  Net('pc inc', pc_l.inc, decoder_a.pc_inc)

  # Memory & IO
  Net('ie ram', mc.ie_ram, ram.ie)
  Net('oe ram', mc.oe_ram, ram.oe)
  Net('ie io', mc.ie_io, io.ie)
  Net('oe io', mc.oe_io, io.oe)
  Net('io mode', mc.io_mode, io.mode)

  for c in components:
    print('{}'.format(type(c)))
    for n in sorted(c.__dict__.keys()):
      s = c.__dict__[n]
      if isinstance(s, Signal):
        if not s.net:
          print('  {}({})'.format(n, s.w))

  try:
    while True:
      clk.tick()
      print('PC: {:2x}{:2x}'.format(pc_h.addr.value(), pc_l.addr.value()))
  except KeyboardInterrupt:
    pass

  print(' '.join('{:x}'.format(b) for b in ram.ram[:256]))

if __name__ == '__main__':
  main()
