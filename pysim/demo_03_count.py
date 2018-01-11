from sim import *

def main():
  # Every clock pulse increments the counter.
  clk = Clock(1)
  counter = Counter(4)

  clk.clk += counter.clk

  for c in (clk, counter,):
    c.reset()

  try:
    for i in range(16):
      print('0b{:04b} 0x{:02x} -- 0x{:02x}'.format(clk.clk.value(), clk.clk.value(), counter.out.value()))
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
