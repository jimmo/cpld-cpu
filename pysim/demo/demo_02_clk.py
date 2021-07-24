from sim import *


def main():
    # 1 bit clock, alternates between 0 and 1.

    clk = Clock(1)  # Try with wider clock bus.

    for c in (clk,):
        c.reset()

    try:
        for i in range(16):
            print(
                "0b{:04b} (0x{:02x})".format(
                    clk.clk.value(),
                    clk.clk.value(),
                )
            )
            clk.tick()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
