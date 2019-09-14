library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

-- The accumulator is an ioregister (see ioregister.vhd) with the following changes:
--   9-bit value, where the MSB represents a carry.
--   `cc` input that clears the carry bit
--   `z` output that is hign when the value is zero.

entity accumulator is
  port (
  input: in std_logic_vector(8 downto 0);
  output: out std_logic_vector(8 downto 0);
  state: out std_logic_vector(8 downto 0);
  z: out std_logic;
  cc: in std_logic;
  nwe: in std_logic;
  noe: in std_logic;
  nrst: in std_logic
  );
end accumulator;

architecture arch of accumulator is
  signal v: std_logic_vector(8 downto 0);
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      v <= "000000000";
    elsif cc = '1' then
      v(8) <= '0';
    elsif falling_edge(nwe) then
      v <= input;
    end if;
  end process;
  output <= v when (noe = '0' and nrst = '1') else (others => 'Z');
  state <= v when (nrst = '1') else (others => 'Z');
  z <= '1' when v(7 downto 0) = "00000000" else '0';
end arch;
