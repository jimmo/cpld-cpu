library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity program_counter is
  port (
  input: in std_logic_vector(7 downto 0);
  output: out std_logic_vector(7 downto 0);
  state: out std_logic_vector(7 downto 0);
  nwe: in std_logic;
  noe: in std_logic;
  nrst: in std_logic;
  inc: in std_logic;
  carry: out std_logic
  );
end program_counter;

architecture arch of program_counter is
  signal v: std_logic_vector(7 downto 0);
  signal load: std_logic_vector(7 downto 0) := "00000000";
  signal offset: std_logic_vector(7 downto 0) := "00000000";
begin
  process (nrst, inc)
  begin
    if nrst = '0' then
      offset <= (others => '0');
      carry <= '0';
    elsif rising_edge(inc) then
      offset <= offset + 1;
      if v = "11111111" then
        carry <= '1';
      else
        carry <= '0';
      end if;
    end if;
  end process;

  process (nrst, nwe)
  begin
    if nrst = '0' then
      load <= (others => '0');
    elsif falling_edge(nwe) then
      load <= input - offset;
    end if;
  end process;

  v <= load + offset;
  output <= v when (noe = '0' and nrst = '1') else (others => 'Z');
  state <= v when (nrst = '1') else (others => 'Z');
end arch;
