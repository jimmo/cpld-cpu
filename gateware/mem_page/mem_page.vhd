library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity mem_page is
  port (
  data: inout std_logic_vector(7 downto 0);
  addr: inout std_logic_vector(12 downto 0);
  z: out std_logic;
  output: out std_logic_vector(5 downto 0);
  nwe: inout std_logic;
  nrst: in std_logic;

  prog_clk: in std_logic;
  prog_data: in std_logic;
  prog_latch: in std_logic
  );
end mem_page;

architecture arch of mem_page is
  -- 0 is input (hi-z), 1 is output.
  signal page0: std_logic_vector(5 downto 0);
  signal page1: std_logic_vector(5 downto 0);
  signal sel_page0: boolean := FALSE;
  signal sel_page1: boolean := FALSE;

  signal prog_addr: std_logic_vector(17 downto 0);
  signal prog_reg: std_logic_vector(7 downto 0);
  signal prog_nwe: std_logic := '1';
begin
  process(nrst, nwe)
  begin
    if (nrst = '0') then
      page0 <= (others => '0');
      page1 <= (others => '0');
    elsif falling_edge(nwe) then
      if sel_page0 then
        page0 <= data(5 downto 0);
      elsif sel_page1 then
        page1 <= data(5 downto 0);
      end if;
    end if;
  end process;

  process(nrst, page0, page1, prog_addr, prog_nwe, prog_reg)
  begin
    if nrst = '0' then
      addr(12) <= 'Z';
      addr(11 downto 0) <= prog_addr(11 downto 0);
      output <= prog_addr(17 downto 12);

      nwe <= prog_nwe;

      data <= prog_reg;
    else
      addr <= (others => 'Z');
      if addr(12) = '0' then
        output <= page0;
      else
        output <= page1;
      end if;

      nwe <= 'Z';

      data <= (others => 'Z');
    end if;
  end process;
  
  z <= '1' when (page0 = "000000" and addr(12 downto 9) = "0111") else '0';
  
  sel_page0 <= (page0 = "000000" and addr(12 downto 9) = "0111") and addr = "0111111110111";
  sel_page1 <= (page0 = "000000" and addr(12 downto 9) = "0111") and addr = "0111111111000";

  process(nrst, prog_clk)
  begin
    if (nrst = '1') then
      prog_addr <= (others => '0');
      prog_reg <= (others => '0');
      prog_nwe <= '1';
    elsif rising_edge(prog_clk) then
      if prog_latch = '1' then
        if prog_nwe = '1' then
          prog_nwe <= '0';
        else
          prog_nwe <= '1';
          prog_addr <= prog_addr + 1;
        end if;
      else
        prog_reg <= prog_reg(6 downto 0) & prog_data;
      end if;
    end if;
  end process;
end arch;
