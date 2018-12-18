library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity mem_index is
  port (
  addr: in std_logic_vector(11 downto 0);
  x: in std_logic_vector(7 downto 0);
  output: out std_logic_vector(11 downto 0);
  en: in std_logic;
  nrst: in std_logic
  );
end mem_index;

architecture arch of mem_index is
begin
  output <= addr when en = '0' else addr + x;
end arch;
