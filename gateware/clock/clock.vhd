library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity clock is
  port (
    led0: out std_logic;
    led1: out std_logic;
    btn_step1: in std_logic;
    btn_step8: in std_logic;
    btn_halt: in std_logic;
    btn_rst: in std_logic;
    btn_s0: in std_logic;
    btn_s1: in std_logic;
    btn_s2: in std_logic;
    btn_s3: in std_logic;
    btn_s4: in std_logic;
    prog4: in std_logic;
    prog5: in std_logic;
    cpu_clk: out std_logic;
    cpu_rst: out std_logic;
    nrst: in std_logic
  );
end clock;

architecture arch of clock is
  signal clk: std_logic := '0';
  signal counter: std_logic_vector(22 downto 0) := "00000000000000000000000";
  signal ring: std_logic_vector(7 downto 0) := "00000000";
  attribute KEEP: string;
  attribute KEEP of ring: signal is "true";
  attribute NOREDUCE: string;
  attribute NOREDUCE of ring: signal is "true";
  signal halt: std_logic := '1';
  signal cycle_count: std_logic_vector(3 downto 0) := "0000";
  signal speed: std_logic_vector(4 downto 0) := "00000";
  signal btn_step1_prev: std_logic := '0';
  signal btn_step8_prev: std_logic := '0';
  signal slow_clk: std_logic := '0';
  signal cpu_clk_int: std_logic := '0';
  signal cpu_clk_prev: std_logic := '0';
begin
  ring <= ring(6 downto 0) & not ring(7) when (nrst = '1') else (others => '0');
  cpu_clk <= cpu_clk_int when halt = '0' else '0';

  led0 <= not (btn_halt and btn_rst and prog4 and btn_step1 and btn_step8 and btn_s0 and btn_s1 and btn_s2);
  led1 <= '0';
  
  process (ring(7))
  begin
    if rising_edge(ring(7)) then
      clk <= not clk;
    end if;
  end process;
  
  process(clk)
  begin
    if rising_edge(clk) then
      if btn_halt = '0' or btn_rst = '0' or prog4 = '0' or cycle_count = "0001" then
        halt <= '1';
        speed <= "00000";
        cycle_count <= "0000";
      end if;
      cpu_rst <= btn_rst and prog4;

      if counter(18) = '1' and slow_clk = '0' then
        if cycle_count = "0000" then
          if btn_step1 = '0' and btn_step1_prev = '1' then
            halt <= '0';
            speed <= "00100";
            cycle_count <= "0010";
          end if;
          btn_step1_prev <= btn_step1;
          if btn_step8 = '0' and btn_step8_prev = '1' then
            halt <= '0';
            speed <= "00100";
            cycle_count <= "1001";
          end if;
          btn_step8_prev <= btn_step8;
        end if;
      end if;
      slow_clk <= counter(18);

      if btn_s0 = '0' then
        halt <= '0';
        speed <= "00001";
      end if;
      if btn_s1 = '0' then
        halt <= '0';
        speed <= "00010";
      end if;
      if btn_s2 = '0' then
        halt <= '0';
        speed <= "00100";
      end if;
      if btn_s3 = '0' then
        halt <= '0';
        speed <= "01000";
      end if;
      if btn_s4 = '0' then
        halt <= '0';
        speed <= "10000";
      end if;

      if halt = '0' and cycle_count /= "0000" then
        if cpu_clk_int = '0' and cpu_clk_prev = '1' then
          cycle_count <= cycle_count - 1;
        end if;
      end if;

      counter <= counter + 1;

      cpu_clk_prev <= cpu_clk_int;
      cpu_clk_int <= (counter(22) and speed(0)) or (counter(20) and speed(1)) or (counter(18) and speed(2)) or (counter(16) and speed(3)) or (counter(14) and speed(4));
    end if;
  end process;
end arch;
