from sim import *

def main():
  clk = Clock(1)
  counter = Counter(4)
  display_counter = Display('counter', 4)
  display_shuffle = Display('shuffle', 4)

  clk.clk += counter.clk

  # Show the counter value
  display_counter.data += counter.out

  # Show a shuffled version of the counter value
  display_shuffle.data += counter.out[(3,1,2,0)]

  for c in (clk, counter, display_counter, display_shuffle,):
    c.reset()

  try:
    for i in range(16):
      # print('0b{:04b} 0x{:02x} -- 0x{:02x}'.format(clk.clk.value(), clk.clk.value(), counter.out.value()))
      clk.tick()
  except KeyboardInterrupt:
    pass


if __name__ == '__main__':
  main()
