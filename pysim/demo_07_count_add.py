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
      print(f'0b{clk.clk.value():04b} (0x{clk.clk.value():02x}) -- 0x{counter.out.value():02x} (0x{counter.out.value():02x}) -- 0x{adder.out.value():02x} (0x{adder.out.value():02x})')
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
