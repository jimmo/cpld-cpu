from sim import *

def main():
  adder = Adder(4)
  power = Power()

  # a = 0111 (7)
  adder.a[0] += power.high
  adder.a[1] += power.high
  adder.a[2] += power.high
  adder.a[3] += power.low

  # b = 0101 (5)
  adder.b[0] += power.high
  adder.b[1] += power.low
  adder.b[2] += power.high
  adder.b[3] += power.low

  for c in (adder, power,):
    c.reset()

  # should be 1100 (12)
  print(f'0b{adder.out.value():04b} (0x{adder.out.value():02x})')


if __name__ == '__main__':
  main()
