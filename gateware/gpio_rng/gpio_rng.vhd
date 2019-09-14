library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

-- GPIO/RNG is a memory mapped device that provides an 11 bidirectional GPIO pins and a (TODO) RNG.
-- This is accessible as four 8-bit registers, all in page 0.
-- DDRA:  111111100
-- PORTA: 111111011
-- DDRB:  111111010
-- PORTB: 111111001

entity gpio_rng is
  port (
  data: inout std_logic_vector(7 downto 0);
  addr: in std_logic_vector(8 downto 0);
  page0: in std_logic;
  gpioa: inout std_logic_vector(7 downto 0);
  gpiob: inout std_logic_vector(2 downto 0);
  nwe: in std_logic;
  noe: in std_logic;
  noe_out: out std_logic;
  nrst: in std_logic
  );
end gpio_rng;

architecture arch of gpio_rng is
  -- 0 is input (hi-z), 1 is output.
  signal ddra: std_logic_vector(7 downto 0);
  signal ddrb: std_logic_vector(2 downto 0);
  signal porta: std_logic_vector(7 downto 0);
  signal portb: std_logic_vector(2 downto 0);
  signal sel_ddra: boolean := FALSE;
  signal sel_ddrb: boolean := FALSE;
  signal sel_porta: boolean := FALSE;
  signal sel_portb: boolean := FALSE;
  signal sel_any: boolean := FALSE;
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      ddra <= (others => '0');
      ddrb <= (others => '0');
      porta <= (others => '0');
      portb <= (others => '0');
    elsif falling_edge(nwe) then
      -- On nWE falling edge, write the current value of the data bus to the appropriate register depending on the currently selected address.
      if sel_ddra then
        ddra <= data;
      elsif sel_ddrb then
        ddrb <= data(2 downto 0);
      elsif sel_porta then
        porta <= data;
      elsif sel_portb then
        portb <= data(2 downto 0);
      end if;
    end if;
  end process;

  -- Figure out whether the current address matches any of our address.
  sel_ddra <= page0 = '1' and addr =  "111111100";
  sel_porta <= page0 = '1' and addr = "111111011";
  sel_ddrb <= page0 = '1' and addr =  "111111010";
  sel_portb <= page0 = '1' and addr = "111111001";
  -- True if any address is currently active.
  sel_any <= sel_ddra or sel_ddrb or sel_porta or sel_portb;
  -- Forward nOE to the next bus device when none of our addresses are active.
  -- This prevents any other device driving the bus when we're active.
  noe_out <= noe when not sel_any else '1';

  process(noe, nwe, sel_any, sel_ddra, sel_ddrb, sel_porta, sel_portb, ddra, ddrb, porta, portb)
  begin
    if noe = '1' or nwe = '0' or not sel_any then
      -- hi-z the data bus when nWE low (write happening), nOE high (no read happening), or not active address.
      data <= (others => 'Z');
    elsif sel_ddra then
      -- Otherwise nOE must be low, so output the current value for the selected address.
      data <= ddra;
    elsif sel_ddrb then
      data <= "00000" & ddrb;
    elsif sel_porta then
      data <= porta;
    elsif sel_portb then
      data <= "00000" & gpiob;  -- TODO: RNG instead of 00000
    else
      -- nOE low but not our address, output zero.
      data <= (others => '0');
    end if;
  end process;

  -- Set the actual GPIO pin to either hi-z (input mode, ddr=0) or the current value (output mode, ddr=1).
  gen_gpioa: for i in 0 to 7 generate
    gpioa(i) <= 'Z' when ddra(i) = '0' else porta(i);
  end generate gen_gpioa;
  gen_gpiob: for i in 0 to 2 generate
    gpiob(i) <= 'Z' when ddrb(i) = '0' else portb(i);
  end generate gen_gpiob;
end arch;
