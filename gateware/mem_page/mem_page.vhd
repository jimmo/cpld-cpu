library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity mem_page is
  port (
  data: inout std_logic_vector(5 downto 0);
  addr: inout std_logic_vector(12 downto 0);
  z: out std_logic;
  output: out std_logic_vector(5 downto 0);
  nwe_out: out std_logic;
  noe_out: out std_logic;
  nwe: in std_logic;
  noe: in std_logic;
  nrst: in std_logic
  );
end mem_page;

architecture arch of mem_page is
  -- 0 is input (hi-z), 1 is output.
  signal page0: std_logic_vector(5 downto 0);
  signal page1: std_logic_vector(5 downto 0);
  signal sel_page0: boolean := FALSE;
  signal sel_page1: boolean := FALSE;
  signal sel_any: boolean := FALSE;
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      page0 <= (others => '0');
      page1 <= (others => '0');
    elsif falling_edge(nwe) then
      if sel_page0 then
        page0 <= data;
      elsif sel_page1 then
        page1 <= data;
      end if;
    end if;
  end process;
  sel_page0 <= addr = "0000011111000";
  sel_page1 <= addr = "0000011111001";
  sel_any <= sel_page0 or sel_page1;

  nwe_out <= nwe when not sel_any else '1';
  noe_out <= noe when not sel_any else '1';

  process(noe, nwe, sel_any, sel_page0, sel_page1, page0, page1)
  begin
    if noe = '1' or nwe = '0' or not sel_any then
      data <= (others => 'Z');
    elsif sel_page0 then
      data <= page0;
    elsif sel_page1 then
      data <= page1;
    else
      data <= (others => '0');
    end if;
  end process;

  output <= page0 when addr(12) = '0' else page1;
  z <= '1' when addr(12 downto 8) = "00000" else '0';
end arch;
