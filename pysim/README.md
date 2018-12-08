## pysim

This is a Python-based logic circuit simulator. It allows you to define "components" which have their pins connected together. Components are defined using VHDL-like sequential and combinatorial statements.

It's designed to support experimentation with simple CPU architectures.

An example multiplexer (combinatorial logic only):

```python
class Multiplexer(Component):
  def __init__(self, name, width=8):
    super().__init__(name)
    self.a = NotifySignal(self, 'a', width)
    self.b = NotifySignal(self, 'b', width)
    self.sel = NotifySignal(self, 'sel', 1)
    self.out = Signal(self, 'out', width)

  def update(self, signal):
    self.out <<= self.a.value() if self.sel.value() == 0 else self.b.value()
```

A simple register:

```python
class Register(Component):
  def __init__(self, name, width=8):
    super().__init__(name)

    self.v = 0

    self.data = Signal(self, 'data', width)
    self.we = NotifySignal(self, 'we', 1)
    self.oe = NotifySignal(self, 'oe', 1)
    self.state = Signal(self, 'state', width)

  def update(self, signal):
    if self.we.had_edge(0, 1):
      self.v = self.data.value()

    self.state <<= self.v

    self.data <<= self.v if self.oe.value() else None
```

Components can be connected together by joining their pins:

```python
m = Multiplexer('m')
r = Register('r')
m.a += r.data
```

Signals can be sliced or indexed to access specific pins:

```python
m = Multiplexer('m')
r = Register('r')
r2 = Register('r2', width=4)
m.sel += r.data[0]
r2.data[0:2] += r.data[4:6]
```

## Examples

### demos

### cpu_a_6

### cpu_a_14

### cpu_ax_5

### cpu_ax_14

### cpu_ah_16
