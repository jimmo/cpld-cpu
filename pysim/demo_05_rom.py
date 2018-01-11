from sim import *

def main():
  clk = Clock(1)
  counter = Counter(16)
  rom = Rom()
  power = Power()

  # 'program' the ROM with some data. (This could be the machine code)
  rom.rom = [0x34, 0x22, 0x97, 0x21, 0x35, 0x82, 0x45, 0x51,] + [0] * 200

  clk.clk += counter.clk

  # Use the counter as the ROM address.
  rom.addr += counter.out

  # Always enable the ROM output.
  rom.oe += power.high

  for c in (clk, counter, rom, power):
    c.reset()

  try:
    for i in range(32):
      print('0b{:04b} 0x{:02x} -- 0x{:02x} -- 0x{:02x}'.format(clk.clk.value(), clk.clk.value(), counter.out.value(), rom.data.value()))
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
