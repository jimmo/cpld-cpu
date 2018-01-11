from sim import *

def main():
  # Every clock pulse increments the counter.
  clk = Clock(1)
  counter = Counter(4)
  adder = Adder(4)
  power = Power()

  clk.clk += counter.clk

  adder.a += counter.out
  adder.b[0] += power.high
  adder.b[1] += power.low
  adder.b[2] += power.low
  adder.b[3] += power.low

  for c in (clk, counter, adder, power,):
    c.reset()

  try:
    for i in range(16):
      print('0b{:04b} (0x{:02x}) -- 0x{:02x} (0x{:02x}) -- 0x{:02x} (0x{:02x})'.format(clk.clk.value(), clk.clk.value(), counter.out.value(), counter.out.value(), adder.out.value(), adder.out.value()))
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
