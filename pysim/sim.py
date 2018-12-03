import math

# Represents a set of connected pins with optional pull up/down.
# Not used directly - when pins connect they create/merge nets.
# When a pin changes state (e.g. into hi-z mode or driving high/low) it calls update
# which will update all connected pins.
class Net():
  net_updates = 0

  def __init__(self, pins):
    self._pins = pins
    self._pull = None

  def name(self):
    return '/'.join(p.fullname() for p in self._pins)

  # Gets a driving pin on this net.
  def driver(self):
    for p in self._pins:
      if not p.is_hiz():
        # Always return the first one. It's not uncommon for there to be multiple drivers
        # while updates propogate, but it should stabilize.
        return p
    return None

  # Called by a pin that is changing state.
  def update(self):
    d = self.driver()

    # Will be None or 0/1.
    v = self._pull

    # If there's no driver and no pull up/down (i.e. the net is floating), then there's
    # nothing to propogate.
    # TODO: this would be worth adding a warning for.
    if not d and not v:
      return

    Net.net_updates += 1
    if d:
      v = d.value()

    # Update all hi-z pins to match the state of the driving pin on this net.
    for p in self._pins:
      if p.is_hiz():
        p.update(v)

  # Add a pin to this net.
  def append(self, p):
    if p in self._pins:
      raise Exception(f'Pin "{p.fullname()}" already in net "{self.name()}"')
    p._net = self
    self._pins.append(p)

  # Merge this net with another (i.e. they share a pin in common).
  def merge(self, n):
    for p in n._pins:
      self.append(p)


# Represents a single wire of a signal (conceptually a single pin of an IC).
# Pins can be wired together into Nets.
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
    # Called when hi-z and something else on this net is driving this pin.
    if v == self._value:
      return
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


# Represents a subset of pins of a signal.
# Typically a Signal's default SignalView will be used which contains all pins.
# A SignalView is useful when individual lines from a bus need to be accessed.
class SignalView():
  def __init__(self, signal, pins):
    self._signal = signal
    self._pins = pins
    self._max = 2**len(self._pins)

  def name(self):
    if self == self._signal._view:
      return self._signal.name()
    else:
      return '{}:{}'.format(self._signal._component.name(), ','.join(p.name() for p in self._pins))

  def __ilshift__(self, v):
    if v is None:
      for p in self._pins:
        p <<= None
    else:
      v = int(v)
      if v < 0:
        raise Exception('invalid value -- {} < 0 for {}'.format(v, self.name()))
      elif v >= self._max:
        raise Exception('invalid value -- {} > {} for {}'.format(v, self._max, self.name()))
      for p in self._pins:
        p <<= (v & 1)
        v >>= 1
    return self

  def __iadd__(self, other):
    #print('connect', self.name(), other.name())
    if len(self._pins) != len(other._pins):
      raise Exception('Mismatched signal widths: {} and {}'.format(self.name(), other.name()))
    for pa, pb in zip(self._pins, other._pins):
      pa += pb
    return self

  def __add__(self, other):
    return self.__iadd__(other)

  def __len__(self):
    return len(self._pins)


# Represents a collection of pins on a component.
# i.e. an 8-bit parallel input would be a signal containing 8 pins.
class Signal():
  def __init__(self, component, name, width):
    self._pins = []
    self._name = name
    self._component = component
    self._notify = False
    for i in range(width):
      self._pins.append(Pin('{}_{}'.format(name, i), self))
    self._view = SignalView(self, self._pins)
    self._last_drive = None

  def name(self):
    if len(self) == 1:
      return self._pins[0].fullname()
    else:
      return '{}:{}[0..{}]'.format(self._component.name(), self._name, len(self)-1)

  def update(self):
    if self._notify:
      self._component.update(signal=self)

  def had_edge(self, i, v):
    return self._pins[i].had_edge(v)

  def value(self):
    v = 0
    for i in range(len(self._pins)):
      v |= (self._pins[i].value() << i)
    return v

  def __ilshift__(self, v):
    # Slightly questionable optimization -- repeated drives of the same signal are ignored.
    if v == self._last_drive:
      return self
    self._last_drive = v

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


# A special case of Signal that notifies the parent component when updated.
class NotifySignal(Signal):
  def __init__(self, component, name, width):
    super().__init__(component, name, width)
    self._notify = True


class Component():
  def __init__(self, name):
    self._name = name

  def name(self):
    return self._name

  def update(self, signal):
    pass

  def reset(self):
    pass

  def info(self):
    n = 0
    for s in self.__dict__.values():
      if isinstance(s, Signal):
        n += len(s)
    # 34 on a XC9572XL
    print(f'{self.name()}: {n} pins')


class Clock(Component):
  def __init__(self, width=1):
    super().__init__('clock')
    self.value = 0
    self.clk = Signal(self, 'clk', width)

  def tick(self):
    self.value = (self.value + 1) % (1 << len(self.clk))
    #print('tick', self.value)
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
    self.clk = NotifySignal(self, 'clk', 1)
    self.out = Signal(self, 'out', w)

  def reset(self):
    self.v = 0
    self.out <<= self.v

  def update(self, signal):
    if self.clk.had_edge(0, 1):
      self.v = (self.v + 1) % (1 << len(self.out))
      self.out <<= self.v


class Register(Component):
  def __init__(self, name, width=8):
    super().__init__(name)
    self.v = 0
    self.data = Signal(self, 'data', width)
    self.ie = NotifySignal(self, 'ie', 1)
    self.oe = NotifySignal(self, 'oe', 1)
    self.state = Signal(self, 'state', width)

  def value(self):
    return self.v

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      self.v = self.data.value()
    self.state <<= self.v
    if self.oe.value():
      self.data <<= self.v
    else:
      self.data <<= None


class SplitRegister(Component):
  def __init__(self, name, width=8, load_width=8):
    super().__init__(name)
    load_width = min(width, load_width)
    self.v = 0
    self.data = Signal(self, 'data', width)
    self.ie = NotifySignal(self, 'ie', width // load_width)
    self.oe = NotifySignal(self, 'oe', 1)
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
    self.a = NotifySignal(self, 'a', width)
    self.b = NotifySignal(self, 'b', width)
    self.a_to_b = NotifySignal(self, 'a_to_b', 1)
    self.b_to_a = NotifySignal(self, 'b_to_a', 1)

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
    self.addr = NotifySignal(self, 'addr', addr_width)
    self.data = Signal(self, 'data', data_width)
    self.oe = NotifySignal(self, 'oe', 1)

  def update(self, signal):
    if self.oe.value():
      self.data <<= self.rom[self.addr.value()]
    else:
      self.data <<= None


class Ram(Component):
  def __init__(self, addr_width=16, data_width=8):
    super().__init__('ram')
    self.ram = [0] * (2**addr_width)
    self.addr = NotifySignal(self, 'addr', addr_width)
    self.data = Signal(self, 'data', data_width)
    self.ie = NotifySignal(self, 'ie', 1)
    self.oe = NotifySignal(self, 'oe', 1)

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      # print('write ram addr', hex(self.addr.value()), 'value', hex(self.data.value()))
      self.ram[self.addr.value()] = self.data.value()

    if self.oe.value():
      # print('read ram addr', hex(self.addr.value()))
      self.data <<= self.ram[self.addr.value()]
    else:
      self.data <<= 0
      self.data <<= None

  def stdout(self):
    print('RAM:')
    skip = False
    for i in range(0, len(self.ram), 16):
      if sum(self.ram[i:i+16]) == 0:
        skip = True
        continue
      if skip:
        print('      ...')
      skip = False
      print('{:04x}: {}'.format(i, ' '.join('{:02x}'.format(b) for b in self.ram[i:i+16])))


class PagedRamController(Component):
  def __init__(self, addr_width=13, num_pages=2, reg_base_addr=None, data_width=8):
    super().__init__('paged-ram')
    self.addr_width = addr_width
    self.page_width = int(math.log2(num_pages))
    self.page_size = 2**(addr_width - self.page_width)
    if reg_base_addr is None:
      self.reg_base_addr = self.page_size - num_pages
    else:
      self.reg_base_addr = reg_base_addr
    self.num_pages = num_pages
    self.in_addr = NotifySignal(self, 'in_addr', addr_width)
    self.out_addr = Signal(self, 'out_addr', data_width)
    self.data = Signal(self, 'data', data_width)
    self.ie = NotifySignal(self, 'ie', 1)
    self.pages = [0] * num_pages

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      page = self.in_addr.value() - self.reg_base_addr
      if page >= 0 and page < self.num_pages:
        print('Page {} = {:02x}'.format(page, self.data.value()))
        self.pages[page] = self.data.value()

    self.out_addr <<= self.pages[self.in_addr.value() >> (self.addr_width - self.page_width)]

        
class Display(Component):
  def __init__(self, n, w):
    super().__init__(n)
    self.data = NotifySignal(self, 'data', w)
    self.last = None

  def update(self, signal):
    if self.last != self.data.value():
      self.last = self.data.value()
      print('{{}} {{:0{}b}}'.format(len(self.data)).format(self.name(), self.last))


class MemDisplay(Component):
  def __init__(self, addr_width=16, data_width=8, data_addr=0, trigger_addr=0):
    super().__init__('mem display')
    self.data_addr = data_addr
    self.trigger_addr = trigger_addr
    self.v = 0
    self.addr = NotifySignal(self, 'addr', addr_width)
    self.data = Signal(self, 'data', data_width)
    self.ie = NotifySignal(self, 'ie', 1)
    self.trigger = 0

  def update(self, signal):
    if self.ie.had_edge(0, 1):
      if self.addr.value() == self.data_addr:
        self.v = self.data.value()
      if self.addr.value() == self.trigger_addr and self.data.value() != self.trigger:
        print(self.v)
        self.trigger = self.data.value()

        
class Adder(Component):
  def __init__(self, w):
    super().__init__('adder')
    self.a = NotifySignal(self, 'a', w)
    self.b = NotifySignal(self, 'b', w)
    self.out = Signal(self, 'out', w)
    self.c = Signal(self, 'c', 1)

  def update(self, signal):
    out = self.a.value() + self.b.value()
    if out >= 2**len(self.a):
      self.c <<= 1
    else:
      self.c <<= 0
    self.out <<= (out % (2**len(self.a)))


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
  reg.ie += counter.out[0]

  for c in (clk, counter, d1, d2, reg,):
    c.reset()

  try:
    for i in range(16):
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
