library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity decoder is
  port (
  instr: in std_logic_vector(2 downto 0);
  state: out std_logic_vector(2 downto 0);
  ram_oe: out std_logic;
  ram_we: out std_logic;
  pc_oe: out std_logic;
  pc_we: out std_logic;
  alu_oe: out std_logic;
  alu_we: out std_logic;
  a_oe: out std_logic;
  a_we: out std_logic;
  x_oe: out std_logic;
  x_we: out std_logic;
  ir_oe: out std_logic;
  ir_we: out std_logic;
  ar_oe: out std_logic;
  ar_we: out std_logic;

  pc_inc: out std_logic;
  idx_en: out std_logic;

  z: in std_logic;
  carry: in std_logic;

  cc: out std_logic;
  
  clk: in std_logic;
  nrst: in std_logic
  );
end decoder;

architecture arch of decoder is
  signal s: unsigned(2 downto 0);
begin
  process(nrst, clk)
  begin
    if (nrst = '0') then
      s <= "000";
    elsif rising_edge(clk) then
      s <= s + 1;
    end if;
  end process;
  
  state <= std_logic_vector(s);

  ram_oe <= '1' when s <= 3 or ((instr = "000" or instr = "001" or instr = "100" or instr = "101") and s <= 5) else '0';

  ar_oe <= '1' when s > 3 else '0';
  ir_oe <= '1' when s > 3 else '0';
  pc_oe <= '1' when s <= 3 else '0';
  ir_we <= '1' when s = 1 else '0';
  pc_inc <= '1' when (s = 2 or s = 4) else '0';
  ar_we <= '1' when s = 3 else '0';

  -- alu
  alu_we <= '1' when (instr = "000" or instr = "001" or instr = "100" or instr = "101") and s = 5 else '0';
  alu_oe <= '1';
  --alu_oe <= '1' when (instr = "000" or instr = "001" or instr = "100" or instr = "101") and (s = 5 or s = 6) else '0';
  a_we <= '1' when (instr = "000" or instr = "001") and s = 6 else '0';
  x_we <= '1' when (instr = "100" or instr = "101") and s = 6 else '0';

  -- sta/stx
  a_oe <= '1' when instr = "010" and (s = 5 or s = 6) else '0';
  x_oe <= '1' when instr = "110" and (s = 5 or s = 6) else '0';
  ram_we <= '1' when (instr = "010" or instr = "110") and s = 6 else '0';

  -- Indexing for alu(a), sta
  idx_en <= '1' when (instr = "000" or instr = "001" or instr = "010") and s > 3 else '0';

  -- jcc c=0 / jnz z=0
  pc_we <= '1' when ((instr = "011" and carry = '0') or (instr = "111" and z = '0')) and s = "101" else '0';
  -- jcc c=1 / jnz z=1
  cc <= '1' when ((instr = "011" and carry /= '0') or (instr = "111" and z = '1')) and s = "101" else '0';
end arch;
