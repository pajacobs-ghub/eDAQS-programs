# pic18f26q71_comms_4_mcu.py
#
# Peter J.
# 2025-11-09: Adapted from pic18f16q41_comms_1.py.
# 2025-11-12: Change LED functions to using utility-pin messages.
# 2026-03-03: Adapted from pic18f26q71_comms_3_mcu to comms_4.
#
import argparse
import time
import re

import sys
sys.path.append("..")
from comms_mcu import rs485

trigger_options = {'positive': 1, 'pos':1, '1':1, 1:1,
                   'negative':0, 'neg':0, '0':0, 0:0}

class PIC18F26Q71_COMMS_4_MCU(object):
    """
    COMMS-MCU service functions are built on RS485 messages.
    """

    __slots__ = ['rs485_node']

    def __init__(self, id_char, serial_port):
        self.rs485_node = rs485.Node(id_char, serial_port)
        return

    def command_COMMS_MCU(self, cmd_txt):
        return self.rs485_node.command(cmd_txt)

    def get_version(self):
        return self.command_COMMS_MCU('v')

    def utility_pins_read_PORT(self):
        txt = self.command_COMMS_MCU(f'u P')
        return int(txt)

    def utility_pins_write_ANSEL(self, val):
        txt = self.command_COMMS_MCU(f'u A {val}')
        return txt

    def utility_pins_write_TRIS(self, val):
        txt = self.command_COMMS_MCU(f'u T {val}')
        return txt

    def utility_pins_write_LAT(self, val):
        txt = self.command_COMMS_MCU(f'u L {val}')
        return txt

    def utility_pins_write_ODC(self, val):
        txt = self.command_COMMS_MCU(f'u O {val}')
        return txt

    def utility_pins_write_WPU(self, val):
        txt = self.command_COMMS_MCU(f'u W {val}')
        return txt

    def i2c_write(self, addr7bit, byte_array):
        cmd_txt = f'b w {addr7bit} {len(byte_array)}'
        for b in byte_array: cmd_txt += f' {b}'
        txt = self.command_COMMS_MCU(cmd_txt)
        if 'error' in txt:
            raise RuntimeError(f"i2c_write error: {txt}")
        items = txt.split()
        if items[0] == 'w':
            addr = int(items[1])
            nbytes = int(items[2])
            bytes_written = [int(item) for item in items[3:]]
        else:
            bytes_written = []
        return bytes_written

    def i2c_read(self, addr7bit, nbytes):
        cmd_txt = f'b r {addr7bit} {nbytes}'
        txt = self.command_COMMS_MCU(cmd_txt)
        if 'error' in txt:
            raise RuntimeError(f"i2c_read error: {txt}")
        items = txt.split()
        if items[0] == 'r':
            addr = int(items[1])
            nbytes = int(items[2])
            bytes_read = [int(item) for item in items[3:]]
        else:
            bytes_read = []
        return bytes_read

    def spi_init(self, upin, ckp, cke, smp):
        cmd_txt = f'c i {upin} {ckp} {cke} {smp}'
        txt = self.command_COMMS_MCU(cmd_txt)
        if 'error' in txt:
            raise RuntimeError(f"spi_init error: {txt}")
        return

    def spi_close(self):
        cmd_txt = 'c c'
        txt = self.command_COMMS_MCU(cmd_txt)
        if 'error' in txt:
            raise RuntimeError(f"spi_close error: {txt}")
        return

    def spi_exchange(self, byte_array):
        cmd_txt = f'c e {len(byte_array)}'
        for b in byte_array: cmd_txt += f' {b}'
        txt = self.command_COMMS_MCU(cmd_txt)
        if 'error' in txt:
            raise RuntimeError(f"spi_exchange error: {txt}")
        items = txt.split()
        if items[0] == 'e':
            nbytes = int(items[2])
            bytes_read = [int(item) for item in items[3:]]
        else:
            bytes_read = []
        return bytes_read

    def analog_read(self, pin):
        # Input:
        # analog channel selector:
        #   0=ANA0 (external trigger signal)
        #   1=ANA1 (V_REF_A)
        #   9=ANB1 (V_REF_B)
        # Returns:
        #   millivolts as an integer
        #
        # We have a 4096mV reference and we are using a 12-bit converter,
        # so the integer count is already in millivolts.
        #
        txt = self.command_COMMS_MCU(f'a {pin}')
        return int(txt)

    def set_V_REF_AB(self, a=255, b=255):
        # Input:
        #   a: 8-bit value for DAC2 to set V_REF_A = 4096mV * a/256
        #   b: 8-bit value for DAC3 to set V_REF_B = 4096mV * b/256
        txt = self.command_COMMS_MCU(f'w {a} {b}')
        return

    def get_V_REF_AB_millivolts(self):
        return [self.analog_read(1), self.analog_read(9)]

    def assert_event_line_low(self):
        txt = self.command_COMMS_MCU('t')
        return

    def release_event_line(self):
        txt = self.command_COMMS_MCU('z')
        return

    def reset_DAQ_MCU(self):
        txt = self.command_COMMS_MCU('R')
        return

    def flush_rx2_buffer(self):
        txt = self.command_COMMS_MCU('F')
        return

    def test_DAQ_MCU_is_ready(self):
        txt = self.command_COMMS_MCU('Q')
        event_txt, ready_txt = txt.split()
        return ready_txt == '1'

    def test_event_has_passed(self):
        txt = self.command_COMMS_MCU('Q')
        event_txt, ready_txt = txt.split()
        return event_txt == '0'

    def enable_external_trigger(self, level, slope):
        '''
        Enable the external-trigger input to the PIC MCU.

        level is an 10-bit integer 0-1023.
        The analog trigger is set at (level/1024 * 4.096) Volts.

        With positive slope the EVENTn line is driven active-low
        when the external voltage exceeds the trigger level.
        With negative slope the EVENTn line is driven active-low
        when the external voltage becomes less than the trigger level.

        The comparator and latch will not be successfully enabled
        if the external-voltage condition already exceeds the level.
        '''
        level = int(level)
        if level < 0: level = 0
        if level > 1023: level = 1023
        slope = trigger_options[slope]
        txt = self.command_COMMS_MCU(f'e {level} {slope}')
        if txt.find('error') >= 0:
            raise RuntimeError('Could not set external trigger.')
        return

    def disable_hardware_trigger(self):
        txt = self.command_COMMS_MCU('d')
        return

    def command_DAQ_MCU(self, cmd_txt):
        '''
        Wraps the cmd_txt as a pass-through-command and sends it.
        Returns the unwrapped response text.

        All interaction with the DAQ-MCU is via these messages
        to the COMMS-MCU.
        '''
        txt = self.command_COMMS_MCU('X%s' % cmd_txt)
        if txt.find('ok') >= 0:
            txt = re.sub('ok', '', txt, count=1).strip()
        else:
            raise RuntimeError(f'DAQ_MCU response not ok: {txt}')
        return txt


if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 pic18f26q71_comms_3_mcu.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'F'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        node1 = PIC18F26Q71_COMMS_4_MCU(node_id, sp)
        print("Just some fiddling around to see that board is alive.")
        # We assume that a LED is attached to RA7
        # bits                                      decimal
        #    7    6    5    4    3    2    1    0    value
        #    X    X    X    X  RA7  RA6  RA5  RA4
        #    0    0    0    0    0    1    1    1  ==  7
        #    0    0    0    0    1    0    0    0  ==  8
        node1.utility_pins_write_ANSEL(7) # RA7 as digital; others analog
        node1.utility_pins_write_TRIS(7) # RA7 as output; others input
        node1.utility_pins_write_LAT(8) # set RA7 high to turn LED on
        print(node1.get_version())
        # If we have been reprogramming the DAQ_MCU while the COMMS_MCU is running,
        # we will likely have rubbish characters in its RX2 buffer.
        if not node1.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node1.reset_DAQ_MCU()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        print(node1.command_DAQ_MCU('v'))
        time.sleep(1.0)
        node1.utility_pins_write_LAT(0) # turn LED off
        print("Adjust the analog reference voltages.")
        node1.set_V_REF_AB(128, 128)
        time.sleep(0.2)
        print(f"millivolts={node1.get_V_REF_AB_millivolts()}")
    else:
        print("Did not find the serial port.")
    print("Done.")
