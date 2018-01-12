from sim import *

def main():
  # 1 bit clock, alternates between 0 and 1.

  clk = Clock(1)  # Try with wider clock bus.

  for c in (clk,):
    c.reset()

  try:
    for i in range(16):
      print(f'0b{clk.clk.value():04b} (0x{clk.clk.value():02x})')
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
