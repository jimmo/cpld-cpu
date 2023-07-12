import machine
import time

speed = 20

# 7-pin programming header is:
# 0  (unused)       Yellow
# 1  clock    Y9    Green
# 2  data     Y10   Blue
# 3  latch    Y11   Purple
# 4  reset    Y12   Grey
# 5  (unused)       White
# GND               Black

 # prog 4
rst = machine.Pin('Y12', mode=machine.Pin.OUT, pull=machine.Pin.PULL_NONE, value=1)

# prog 1
clk = machine.Pin('Y9', mode=machine.Pin.OUT, pull=machine.Pin.PULL_NONE)
# prog 2
data = machine.Pin('Y10', mode=machine.Pin.OUT, pull=machine.Pin.PULL_NONE)
# prog 3
latch = machine.Pin('Y11', mode=machine.Pin.OUT, pull=machine.Pin.PULL_NONE)

def reset():
  rst.value(0)
  rst.value(1)

def pgm(on=True):
  if on:
    rst.value(0)
  else:
    rst.value(1)

def send(x):
  clk.value(0)
  latch.value(0)

  for i in range(8):
    bit = (x >> (7-i)) & 1
    data.value(bit)
    clk.value(1)
    clk.value(0)
    time.sleep_us(speed)

  latch.value(1)
  clk.value(1)
  clk.value(0)
  time.sleep_us(speed)
  clk.value(1)
  clk.value(0)
  time.sleep_us(speed)
  latch.value(0)


def erase():
  reset()
  pgm(True)
  for i in range(10000):
    send(0)
  pgm(False)
  reset()
  reset()


def load(data):
  reset()
  pgm(True)
  for b in data:
    send(b)
  pgm(False)
  reset()
  reset()

