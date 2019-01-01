library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity alu is
  port (
  a: in std_logic_vector(8 downto 0);
  b: in std_logic_vector(7 downto 0);
  output: out std_logic_vector(8 downto 0);
  fn: in std_logic;
  nwe: in std_logic;
  noe: in std_logic;
  nrst: in std_logic
  );
end alu;

architecture arch of alu is
  signal v: std_logic_vector(8 downto 0);
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      v <= "000000000";
    elsif falling_edge(nwe) then
      if fn = '0' then
        v <= a(8) & not (a(7 downto 0) or b);
      else
        v <= ('0' & a(7 downto 0)) + ('0' & b);
      end if;
    end if;
  end process;
  output <= v when (noe = '0' and nrst = '1') else (others => 'Z');
end arch;
