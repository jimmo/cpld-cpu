from sim import *

def main():
  clk = Clock(1)
  counter = Counter(4)
  reg = Register('reg', 4)

  clk.clk += counter.clk
  reg.data += counter.out

  # Latch the register every time the 3rd bit of the counter goes high.
  reg.ie += counter.out[2]

  for c in (clk, counter, reg,):
    c.reset()

  try:
    for i in range(16):
      print('0b{:04b} 0x{:02x} -- 0b{:04b} 0x{:02x} -- 0b{:04b} 0x{:02x}'.format(clk.clk.value(), clk.clk.value(), counter.out.value(), counter.out.value(), reg.state.value(), reg.state.value()))
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
