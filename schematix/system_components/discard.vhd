--name: discard
--tag: schematic
--input: in1
--source_file: built_in

---Discard
---=======
---Discard all data on *in1*. Usefull to avoid unconnected outputs.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use std.textio.all;

entity discard is

  port(
    CLK     : in std_logic;
    RST     : in std_logic;
   
    IN1     : in std_logic_vector(15 downto 0);
    IN1_STB : in std_logic;
    IN1_ACK : out std_logic
  );

end entity discard;

architecture RTL of discard is
begin

  IN1_ACK <= '1';

end RTL;
