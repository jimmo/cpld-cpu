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
      print(f'0b{clk.clk.value():04b} 0x{clk.clk.value():02x} -- 0x{counter.out.value():02x} -- 0x{rom.data.value():02x}')
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
