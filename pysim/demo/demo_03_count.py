from sim import *


def main():
    # Every clock pulse increments the counter.
    clk = Clock(1)
    counter = Counter(4)

    clk.clk += counter.clk

    for c in (
        clk,
        counter,
    ):
        c.reset()

    try:
        for i in range(16):
            print(
                f"0b{clk.clk.value():04b} 0x{clk.clk.value():02x} -- 0x{counter.out.value():02x}"
            )
            clk.tick()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
