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
      print(f'0b{clk.clk.value():04b} 0x{clk.clk.value():02x} -- 0b{counter.out.value():04b} 0x{counter.out.value():02x} -- 0b{reg.state.value():04b} 0x{reg.state.value():02x}')
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
