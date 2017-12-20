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


class Net():
  def __init__(self, pins):
    self._pins = pins
    self._pull = None

  def name(self):
    return '/'.join(p.fullname() for p in self._pins)

  def driver(self):
    d = None
    for p in self._pins:
      if not p.is_hiz():
        if d:
          #print(f'Multiple drivers for net "{self.name()}" -- "{d.fullname()}" and "{p.fullname()}"')
          return None
        d = p
    return d

  def update(self):
    d = self.driver()
    v = self._pull
    if not d and not v:
      return
      #raise Exception(f'Floating net with no pull-up/down "{self.name()}"')
    if d:
      v = d.value()
    for p in self._pins:
      if p.is_hiz():
        p.update(v)

  def append(self, p):
    if p in self._pins:
      raise Exception(f'Pin "{p.fullname()}" already in net "{self.name()}"')
    p._net = self
    self._pins.append(p)

  def merge(self, n):
    for p in n._pins:
      self.append(p)


class Pin():
  def __init__(self, name, signal):
    self._name = name
    self._signal = signal
    self._net = None
    self._value = 0
    self._hiz = True
    self._edge = None

  def name(self):
    return self._name

  def fullname(self):
    return f'{self._signal._component.name()}:{self.name()}'

  def is_hiz(self):
    return self._hiz

  def value(self):
    return self._value

  def update(self, v):
    if v != self._value:
      self._edge = v
    self._value = v
    self._signal.update()

  def had_edge(self, e):
    result = self._edge == e
    self._edge = None
    return result

  def __ilshift__(self, v):
    if not self._hiz and v == self._value:
      return self
    if self._hiz and v is None:
      return self
    #print(f'drive "{self.fullname()}" to {v}')
    self._value = v
    self._hiz = v is None
    if self._net:
      self._net.update()
    #else:
    #  print(f'Warning: driving unconnected pin {self.fullname()}')
    return self

  def __iadd__(self, other):
    if self._net and other._net:
      self._net.merge(other._net)
      other._net = self._net
    elif self._net:
      self._net.append(other)
      other._net = self._net
    elif other._net:
      other._net.append(self)
      self._net = other._net
    else:
      self._net = Net([self, other])
      other._net = self._net
    return self

  def __add__(self, other):
    return self.__iadd__(other)


class SignalView():
  def __init__(self, signal, pins):
    self._signal = signal
    self._pins = pins

  def name(self):
    if self == self._signal._view:
      return self._signal.name()
    else:
      return '{}:{}'.format(self._signal._component.name(), ','.join(p.name() for p in self._pins))

  def __ilshift__(self, v):
    if v is None:
      for i in range(len(self._pins)):
        self._pins[i] <<= None
    else:
      v = int(v)
      if v < 0:
        raise Exception('invalid value -- underflow')
      elif v >= 2**len(self._pins):
        raise Exception('invalid value -- overflow')
      for i in range(len(self._pins)):
        self._pins[i] <<= (v & 1)
        v >>= 1
    return self

  def __iadd__(self, other):
    print('connect', self.name(), other.name())
    if len(self._pins) != len(other._pins):
      raise Exception('Mismatched signal widths: {} and {}'.format(self.name(), other.name()))
    for pa, pb in zip(self._pins, other._pins):
      pa += pb
    return self

  def __add__(self, other):
    return self.__iadd__(other)

  def __len__(self):
    return len(self._pins)


class Signal():
  def __init__(self, component, name, width):
    self._pins = []
    self._name = name
    self._component = component
    for i in range(width):
      self._pins.append(Pin('{}_{}'.format(name, i), self))
    self._view = SignalView(self, self._pins)

  def name(self):
    if len(self) == 1:
      return self._pins[0].fullname()
    else:
      return '{}:{}[0..{}]'.format(self._component.name(), self._name, len(self)-1)

  def update(self):
    self._component.update(signal=self)

  def had_edge(self, i, v):
    return self._pins[i].had_edge(v)

  def value(self):
    v = 0
    for i in range(len(self)):
      v |= (self._pins[i].value() << i)
    return v

  def __ilshift__(self, v):
    self._view <<= v
    return self

  def __getitem__(self, i):
    if isinstance(i, slice):
      return SignalView(self, self._pins[i])
    elif isinstance(i, tuple):
      return SignalView(self, [self._pins[n] for n in i])
    else:
      return SignalView(self, [self._pins[i]])

  def __setitem__(self, i, value):
    # Required to make `a.b[n] += c.d[m]` work
    pass

  def __iadd__(self, other):
    self._view += other
    return self

  def __add__(self, other):
    return self.__iadd__(other)

  def __len__(self):
    return len(self._pins)


class Component():
  def __init__(self, name):
    self._name = name

  def name(self):
    return self._name

  def update(self, signal):
    pass

  def reset(self):
    pass


class Clock(Component):
  def __init__(self, width=1):
    super().__init__('clock')
    self.value = 0
    self.clk = Signal(self, 'clk', width)

  def tick(self):
    print('tick')
    self.value = (self.value + 1) % (1 << len(self.clk))
    self.clk <<= self.value

  def reset(self):
    self.value = 0
    self.clk <<= self.value


class Power(Component):
  def __init__(self):
    super().__init__('power')
    self.low = Signal(self, 'low', 1)
    self.high = Signal(self, 'high', 1)

  def reset(self):
    self.low <<= 0
    self.high <<= 1

class Counter(Component):
  def __init__(self, w):
    super().__init__('counter')
    self.v = 0
    self.clk = Signal(self, 'clk', 1)
    self.out = Signal(self, 'out', w)

  def reset(self):
    self.v = 0
    self.out <<= self.v

  def update(self, signal):
    if self.clk.had_edge(0, 1):
      self.v = (self.v + 1) % (1 << len(self.out))
      self.out <<= self.v


class Register(Component):
  def __init__(self, name, width=8, load_width=8):
    super().__init__(name)
    self.v = 0
    self.data = Signal(self, 'data', width)
    self.ie = Signal(self, 'ie', width // load_width)
    self.oe = Signal(self, 'oe', 1)
    self.state = Signal(self, 'state', width)

  def value(self):
    return self.v

  def update(self, signal):
    load_width = len(self.data) // len(self.ie)
    mask = (1 << load_width) - 1
    for i in range(len(self.ie)):
      if self.ie.had_edge(i, 1):
        self.v = (self.v & ~mask) | (self.data.value() & mask)
      mask <<= load_width
    self.state <<= self.v
    if self.oe.value():
      self.data <<= self.v
    else:
      self.data <<= None


class BusConnect(Component):
  def __init__(self, name, width=8):
    super().__init__(name)
    self.a = Signal(self, 'a', width)
    self.b = Signal(self, 'b', width)
    self.a_to_b = Signal(self, 'a_to_b', 1)
    self.b_to_a = Signal(self, 'b_to_a', 1)

  def update(self, signal):
    if self.a_to_b.value():
      #print('a to b', self.a.value())
      self.b <<= self.a.value()
    else:
      self.b <<= None

    if self.b_to_a.value():
      #print('b to a', self.b.value())
      self.a <<= self.b.value()
    else:
      self.a <<= None


class Rom(Component):
  def __init__(self, addr_width=16, data_width=8):
    super().__init__('rom')
    self.rom = [0] * (2**addr_width)
    self.addr = Signal(self, 'addr', addr_width)
    self.data = Signal(self, 'data', data_width)
    self.oe = Signal(self, 'oe', 1)

  def update(self, signal):
    if self.oe.value():
      self.data <<= self.rom[self.addr.value()]
    else:
      self.data <<= None


class Ram(Component):
  def __init__(self, addr_width=16, data_width=8):
    super().__init__('ram')
    self.ram = [0] * (2**addr_width)
    self.addr = Signal(self, 'addr', addr_width)
    self.data = Signal(self, 'data', data_width)
    self.ie = Signal(self, 'ie', 1)
    self.oe = Signal(self, 'oe', 1)

  def update(self, signal):
    if self.ie.value():
      self.ram[self.addr.value()] = self.data.value()

    if self.oe.value():
      self.data <<= self.ram[self.addr.value()]
    else:
      self.data <<= None


class Display(Component):
  def __init__(self, n, w):
    super().__init__(n)
    self.data = Signal(self, 'data', w)
    self.last = None

  def update(self, signal):
    if self.last != self.data.value():
      self.last = self.data.value()
      print('{{}} {{:0{}b}}'.format(len(self.data)).format(self.name(), self.last))


def main():
  clk = Clock(1)
  counter = Counter(8)
  d1 = Display('counter', 8)
  d2 = Display('shuffle', 8)
  reg = Register('a', 4)

  counter.clk += clk.clk[0]
  d1.data += counter.out
  d2.data += counter.out[(7,6,5,4,3,2,1,0)]

  reg.data += counter.out[0:4]
  reg.ie[0] += reg.ie[1] + counter.out[0]

  for c in (clk, counter, d1, d2, reg,):
    c.reset()

  try:
    for i in range(16):
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
