library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity program_counter_high is
  port (
  input: in std_logic_vector(4 downto 0);
  output: out std_logic_vector(7 downto 0);
  state: out std_logic_vector(7 downto 0);
  nwe: in std_logic;
  noe: in std_logic;
  nrst: in std_logic;
  inc: in std_logic;
  carry: out std_logic
  );
end program_counter_high;

architecture arch of program_counter_high is
  signal clk: std_logic := '0';
  signal ring: std_logic_vector(7 downto 0) := "00000000";
  attribute KEEP: string;
  attribute KEEP of ring: signal is "true";
  attribute NOREDUCE: string;
  attribute NOREDUCE of ring: signal is "true";

  signal v: std_logic_vector(7 downto 0) := "00000000";

  signal nwe_p: std_logic := '0';
  signal inc_p: std_logic := '0';
begin
  ring <= ring(6 downto 0) & not ring(7) when (nrst = '1') else (others => '0');

  process (ring)
  begin
    if rising_edge(ring(7)) then
      clk <= not clk;
    end if;
  end process;
  
  process (nrst, clk)
  begin
    if nrst = '0' then
      v <= (others => '0');
      carry <= '0';
    elsif rising_edge(clk) then
      if nwe = '0' and nwe_p = '1' then
        v <= "000" & input;
      elsif inc = '1' and inc_p = '0' then
        v <= v + 1;
        if v = "11111111" then
          carry <= '1';
        else
          carry <= '0';
        end if;
      end if;
      nwe_p <= nwe;
      inc_p <= inc;
    end if;
  end process;

  output <= v when (noe = '0' and nrst = '1') else (others => 'Z');
  state <= v when (nrst = '1') else (others => 'Z');
end arch;
