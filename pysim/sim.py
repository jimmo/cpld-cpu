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



  # def reset(self):
  #   print('Disconnected signals')
  #   depth(1)
  #   for c in self._components:
  #     debug('{}'.format(type(c)))
  #     for n in sorted(c.__dict__.keys()):
  #       s = c.__dict__[n]
  #       if isinstance(s, Signal):
  #         if not s.net:
  #           debug('  {}({})'.format(n, s.w))
  #   depth(-1)


# Represents either a pin (or set of pins) on a component.
# Multiple signals are joined together in a Net.
class Signal():
  def __init__(self, p, w):
    # Parent component.
    self._parent = p
    # Width of this signal (i.e. number of bits).
    self._w = w
    # Current value (0..2^w-1).
    self._v = 0
    # Net that this signal is connected to.
    self._net = None
    # True if this signal is not currently driving the net.
    self._hiz = True
    # TODO
    self._edge = None

  def name(self):
    for n, s in self._parent.__dict__.items():
      if s == self:
        return self._parent.name() + '::' + n
    return 'unknown'

  def width(self):
    return self._w

  def net(self):
    return self._net

  def is_hiz(self):
    return self._hiz

  # Called by the parent component (usually in update()) to either
  # drive the pin (v = 0 or 1) or set it to hi-z mode ( v= None).
  # All other singals on this net will be updated.
  def drive(self, v):
    depth(1)
    if v is not None and (v < 0 or v >= 2**self._w):
      print('Driving "{}/{}/{}" to "{}" invalid value for {}bit signal.'.format(self._net.name, self._parent.name(), self.name(), v, self._w))
    #debug('driving "{}/{}/{}" to "{}" (was "{}/{}")'.format(self._net.name, self._parent.name, self.name(), v, 'hiz' if self._hiz else 'loz', self._v))
    # Do nothing for no-op changes.
    if v is None:
      if not self._hiz:
        #debug('hiz mode')
        self._hiz = True
        self._net.update()
      #else:
      #  debug('ignore (same-hiz)')
    else:
      if self._v != v or self._hiz:
        #debug('driving mode')
        self._hiz = False
        self._v = v
        if self._net:
          self._net.update()
      #else:
      #  debug('ignore (same-v)')
    depth(-1)

  # Called by the net that this signal is connected to when another signal changes.
  def follow(self):
    depth(1)
    v = self._net.value()
    if v and not self._v:
      self._edge = 1
    if not v and self._v:
      self._edge = 0
    self._v = v
    #debug('following "{}/{}/{}" to "{}"'.format(self._net.name, self._parent.name, self.name(), v))
    if not self._hiz:
      debug('tried to follow a loz signal')
    self._parent.update()
    depth(-1)

  # Returns true if this signal had an edge since the last call.
  def was_edge(self, e):
    r = self._edge == e
    self._edge = None
    return r

  def value(self):
    if self._hiz:
      if self._net:
        return self._net.value()
      else:
        raise Exception('signal "{}" is floating'.format(self.name()))
    else:
      return self._v

  def select(self, *n):
    s = Select(self, *n)
    Net('{}_{}'.format(self.name(), '_'.join(map(str, n))), self, s.inp)
    return s.out

  def connect(self, *signals):
    Net(self.name() + ',' + ','.join(s.name() for s in signals), *[self] + list(signals))


# Represents a set of connected signals.
class Net:
  def __init__(self, name, *signals):
    self._n = name

    # Check that all signals on this net are the same width.
    w_min, w_max = min(s.width() for s in signals), max(s.width() for s in signals)
    if w_min != w_max:
      raise Exception('Mismatched signal widths [{}] on net "{}".'.format(','.join(str(s.width()) for s in signals), self._n))

    self._w = w_min
    self._signals = list(signals)

    # Connect all signals to this net, and if any signals are already connected to nets,
    # join them into this one.
    for s in list(self._signals):
      if s.net():
        self._join(s.net())
      s._net = self

  def _join(self, other):
    for s in other._signals:
      #debug('moving {}.{} to {}'.format(other.name, s.name(), self._n))
      s._net = self
      self._signals.append(s)

  def value(self):
    # Find the current driver.
    driver = None
    for s in self._signals:
      if not s.is_hiz():
        if driver is not None:
          debug('Two drivers on net "{}"'.format(self._n))
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
    #debug('updating net "{}"'.format(self._n))
    # Find the current driver.
    driver = None
    for s in self._signals:
      if s.is_hiz():
        s.follow()
    depth(-1)


# Base class for all components.
class Component:
  def __init__(self, n):
    self._n = n

  def name(self):
    return self._n

  def update(self):
    pass

  def reset(self):
    pass


class Select(Component):
  N = 0
  LOW = object()
  HIGH = object()
  def __init__(self, s, *n):
    super().__init__('select_{}'.format(Select.N))
    self.inp = Signal(self, s.width())
    self.out = Signal(self, len(n))
    self.n = n

  def update(self):
    v = 0
    #print(self.inp.value(), self.n)
    for i in range(len(self.n)):
      if self.n[i] == Select.LOW:
        continue
      elif self.n[i] == Select.HIGH or (self.inp.value() >> self.n[i]) & 1:
        v |= (1 << i)
    #print(v)
    self.out.drive(v)


class Clock(Component):
  def __init__(self, w=1):
    super().__init__('clock')
    self.v = 0
    self.w = w
    self.clk = Signal(self, w)

  def tick(self):
    debug('tick')
    self.v = (self.v + 1) % (1 << self.w)
    self.clk.drive(self.v)

  def update(self):
    pass

  def reset(self):
    self.clk.drive(0)


class Counter(Component):
  def __init__(self, w):
    super().__init__('counter')
    self.v = 0
    self.w = w
    self.clk = Signal(self, 1)
    self.out = Signal(self, w)

  def reset(self):
    self.out.drive(self.v)

  def update(self):
    if self.clk.was_edge(1):
      self.v = (self.v + 1) % (1 << self.w)
      self.out.drive(self.v)

  def reset(self):
    self.out.drive(0)


class Register(Component):
  def __init__(self, n, w=8):
    super().__init__('register_' + n)
    self.v = 0
    self.data = Signal(self, w)
    self.ie_l = Signal(self, 1)
    self.ie_h = Signal(self, 1)
    self.oe = Signal(self, 1)

  def update(self):
    depth(1)
    if self.ie_l.was_edge(1):
      print(f'{self.name} load low 0x{self.data.v:1x} (was {self.v})')
      self.v = (self.v & 0xf0) | (self.data.v & 0x0f)
    if self.ie_h.was_edge(1):
      print(f'{self.name} load high 0x{self.data.v:1x} (was {self.v})')
      self.v = (self.data.v & 0xf0) | (self.v & 0x0f)
    if self.oe.value():
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


class Rom(Component):
  def __init__(self):
    super().__init__('rom')
    self.rom = [0] * 65536
    #self.rom[0] = Inst.load('al', 0xa)
    #self.rom[1] = Inst.load('ah', 0x1)
    #self.rom[2] = Inst.load('bl', 0xb)
    #self.rom[3] = Inst.load('bh', 0x7)
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


class Display(Component):
  def __init__(self, n, w):
    super().__init__(n)
    self.data = Signal(self, w)

  def update(self):
    print('{{}} {{:0{}b}}'.format(self.data.width()).format(self.name(), self.data.value()))

def main():
  clk = Clock(6)
  counter = Counter(8)
  disp = Display('status', 8)
  disp2 = Display('disp_sel', 7)
  reg = Register('a', 4)

  clk.clk.select(0).connect(counter.clk)
  counter.out.connect(disp.data)
  counter.out.select(Select.HIGH, 0, 2, 1, 3, Select.HIGH, Select.LOW).connect(disp2.data)
  #reg.data.connect(counter.out.select(0,1,2,3))
  #reg.ie_l.connect(reg.ie_h, counter.out.select(2))

  # todo - either add oe to counter or some sort of bus driver.
  #sim.connect('regoe', reg.

  for c in (clk, counter, disp, disp2, reg,):
    c.reset()

  try:
    for i in range(16):
      clk.tick()
      #print(counter.out.value())
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
