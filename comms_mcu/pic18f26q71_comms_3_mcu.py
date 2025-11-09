# pic18f26q71_comms_3_mcu.py
#
# Peter J.
# 2025-11-09: Adapted from pic18f16q41_comms_1.py.
#
import argparse
import time
import re

import sys
sys.path.append("..")
from comms_mcu import rs485

class PIC18F26Q71_COMMS_3_MCU(object):
    """
    COMMS-MCU service functions are built on RS485 messages.
    """

    __slots__ = ['rs485_node']

    def __init__(self, id_char, serial_port):
        self.rs485_node = rs485.Node(id_char, serial_port)
        return

    def get_version(self):
        return self.rs485_node.command('v')

    def set_LED(self, val):
        txt = self.rs485_node.command(f'L{val}')
        return

    def assert_event_line_low(self):
        txt = self.rs485_node.command('t')
        return

    def release_event_line(self):
        txt = self.rs485_node.command('z')
        return

    def reset_DAQ_MCU(self):
        txt = self.rs485_node.command('R')
        return

    def flush_rx2_buffer(self):
        txt = self.rs485_node.command('F')
        return

    def test_DAQ_MCU_is_ready(self):
        txt = self.rs485_node.command('Q')
        event_txt, ready_txt = txt.split()
        return ready_txt == '1'

    def test_event_has_passed(self):
        txt = self.rs485_node.command('Q')
        event_txt, ready_txt = txt.split()
        return event_txt == '0'

    def enable_external_trigger(self, level, slope):
        '''
        Enable the external-trigger input to the PIC MCU.

        level is an 8-bit integer 0-255.
        The analog trigger is set at (level/256 * 2.048) Volts.

        With positive slope the EVENTn line is driven active-low
        when the external voltage exceeds the trigger level.
        With negative slope the EVENTn line is driven active-low
        when the external voltage becomes less than the trigger level.

        The comparator and latch will not be successfully enabled
        if the external-voltage condition already exceeds the level.
        '''
        level = int(level)
        if level < 0: level = 0
        if level > 255: level = 255
        options = {'positive': 1, 'pos':1, '1':1, 1:1,
                   'negative':0, 'neg':0, '0':0, 0:0}
        slope = options[slope]
        txt = self.rs485_node.command(f'e {level} {slope}')
        if txt.find('error') >= 0:
            raise RuntimeError('Could not set external trigger.')
        return

    def enable_internal_trigger(self, level, slope):
        '''
        Enable the internal-trigger input to the PIC MCU.
        The analog signal comes from channel 0 buffer amplifier.

        level is an 8-bit integer 0-255.
        The analog trigger is set at (level/256 * 2.048) Volts.

        With positive slope the EVENTn line is driven active-low
        when the channel 0 voltage exceeds the trigger level.
        With negative slope the EVENTn line is driven active-low
        when the channel 0 voltage becomes less than the trigger level.

        The comparator and latch will not be successfully enabled
        if the channel 0 voltage condition already exceeds the level.
        '''
        level = int(level)
        if level < 0: level = 0
        if level > 255: level = 255
        options = {'positive': 1, 'pos':1, '1':1, 1:1,
                   'negative':0, 'neg':0, '0':0, 0:0}
        slope = options[slope]
        txt = self.rs485_node.command(f'i {level} {slope}')
        if txt.find('error') >= 0:
            raise RuntimeError('Could not set internal trigger.')
        return

    def disable_trigger(self):
        txt = self.rs485_node.command(f'd')
        return

    def command_COMMS_MCU(self, cmd_txt):
        return self.rs485_node.command(cmd_txt)

    def command_DAQ_MCU(self, cmd_txt):
        '''
        Wraps the cmd_txt as a pass-through-command and sends it.
        Returns the unwrapped response text.

        All interaction with the DAQ-MCU is via these messages
        to the COMMS-MCU.
        '''
        txt = self.rs485_node.command('X%s' % cmd_txt)
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
    node_id = 'E'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        node1 = PIC18F26Q71_COMMS_3_MCU(node_id, sp)
        print("Just some fiddling around to see that board is alive.")
        # We assume that a LED is attached to RA6
        node1.set_LED(1)
        print(node1.get_version())
        # If we have been reprogramming the DAQ_MCU while the COMMS_MCU is running,
        # we will likely have rubbish characters in its RX2 buffer.
        if not node1.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node1.reset_DAQ_MCU()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        # print(node1.command_DAQ_MCU('v'))
        time.sleep(1.0)
        node1.set_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
