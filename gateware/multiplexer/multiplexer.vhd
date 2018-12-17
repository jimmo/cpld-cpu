library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity multiplexer is
  port (
  a: in std_logic_vector(7 downto 0);
  b: in std_logic_vector(7 downto 0);
  output: out std_logic_vector(7 downto 0);
  sel: in std_logic;
  nrst: in std_logic
  );
end multiplexer;

architecture arch of multiplexer is
begin
  output <= a when sel = '0' else b;
end arch;
