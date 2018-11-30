class Logic(Component):
  def __init__(self):
    super().__init__('logic')
    self.a = NotifySignal(self, 'a', 8)
    self.b = NotifySignal(self, 'b', 8)
    self.fn = NotifySignal(self, 'fn', 3)
    self.out = Signal(self, 'out', 8)
    self.oe = NotifySignal(self, 'oe', 1)

  def update(self, signal):
    if self.oe.value():
      a = self.a.value()
      b = self.b.value()
      fn = self.fn.value()
      
      if fn == 0:
        # nor
        o = ~(a | b)
      elif fn == 1:
        # add
        o = a + b
      elif fn == 2:
        # shr
        o = 0

      self.out <<= (o & 0xff)
    else:
      self.out <<= None    


class ProgramCounter(Component):
  def __init__(self):
    super().__init__('pc')
    self.v = 0
    self.addr = Signal(self, 'addr', 14)
    self.data = Signal(self, 'data', 14)
    self.rst = NotifySignal(self, 'rst', 1)
    self.inc = NotifySignal(self, 'inc', 1)
    self.ie = NotifySignal(self, 'ie', 1)

  def update(self, signal):
    if self.rst.value() == 1:
      self.v = 0
    elif self.ie.value():
      self.v = self.data.value()
    elif self.inc.had_edge(0, 1):
      if self.v == 2 ** 13 - 1:
        self.v = 0
      else:
        self.v += 1
    self.addr <<= self.v

