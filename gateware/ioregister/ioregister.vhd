library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

-- ioregister is an 8-bit register.
--   value is set to zero and all pins are hi-z when nRST is low.
--   value is loaded from `input` on falling edge of nWE.
--   value is set on `output` when nOE is low, hi-z otherwise.
--   value is always set on `state`.

entity ioregister is
  port (
  input: in std_logic_vector(7 downto 0);
  output: out std_logic_vector(7 downto 0);
  state: out std_logic_vector(7 downto 0);
  nwe: in std_logic;
  noe: in std_logic;
  nrst: in std_logic
  );
end ioregister;

architecture arch of ioregister is
  -- Register value.
  signal v: std_logic_vector(7 downto 0);
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      -- Reset value when held in reset.
      v <= "00000000";
    elsif falling_edge(nwe) then
      -- Load value from `input` bus on falling edge of nWE.
      v <= input;
    end if;
  end process;
  -- Output when nOE low and not in reset. hi-z all other cases.
  output <= v when (noe = '0' and nrst = '1') else (others => 'Z');
  -- Always put current value on `state` (unless in reset).
  state <= v when (nrst = '1') else (others => 'Z');
end arch;
