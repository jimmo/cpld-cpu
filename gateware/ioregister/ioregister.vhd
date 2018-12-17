library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

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
  signal v: std_logic_vector(7 downto 0);
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      v <= "00000000";
    elsif falling_edge(nwe) then
      v <= input;
    end if;
  end process;
  output <= v when (noe = '0' and nrst = '1') else (others => 'Z');
  state <= v when (nrst = '1') else (others => 'Z');
end arch;
