--name: constant_value
--tag: sources
--output: out1 : get_bits(component["parameters"]["value"])
--source_file: built_in
--parameter: value: 0

---Constant Value
---==============
---
---Output constant value repeatedly.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity constant_value is

  generic(
    VALUE       : integer
  );
  port(
    CLK         : in  std_logic;
    RST         : in  std_logic;
    
    OUT1        : out std_logic_vector(15 downto 0);
    OUT1_STB    : out std_logic;
    OUT1_ACK    : in  std_logic
  );

end entity constant_value;

architecture RTL of constant_value is

begin

    OUT1 <= std_logic_vector(to_signed(VALUE, 16));
    OUT1_STB <= '1';

end architecture RTL;
