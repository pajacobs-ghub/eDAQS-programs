# pic18f16q41_comms_1_mcu.py
#
# Peter J.
# 2025-10-20: Extracted from v1 code.
#
import argparse
import time
import re
import struct

import sys
sys.path.append("..")
from comms_mcu import rs485

class PIC18F16Q41_COMMS_1_MCU:
    """
    COMMS-MCU service functions are built on RS485 messages.
    """

    __slots__ = ['rs485']

    def __init__(self, id_char, serial_port):
        self.rs485 = rs485.Node(id_char, serial_port)
        return

    def command(self, cmd_txt):
        '''
        Sends the text of a command to the RS485 send function.
        Returns the text of the RS485 return message.

        Each command to the PIC MCU is encoded as the first character
        of the command text. Any required data follows that character.

        A return message should start with the same command character
        and may have more text following that character.
        A command that is not successful should send back a message
        with the word "error" in it, together with some more information.
        '''
        cmd_char = cmd_txt[0]
        self.rs485.send_command(cmd_txt)
        txt = self.rs485.get_response()
        if not txt.startswith(cmd_char):
            raise RuntimeError(f'Unexpected response: {txt}')
        txt = re.sub(cmd_char, '', txt, count=1).strip()
        if txt.find('error') >= 0:
            print("Warning: error return for command to COMMS-MCU.")
            print(f"  cmd_txt: {cmd_txt}")
            print(f"  response: {txt}")
        return txt

    def get_version(self):
        return self.command('v')

    def set_LED(self, val):
        txt = self.command(f'L{val}')
        return

    def assert_event_line_low(self):
        txt = self.command('t')
        return

    def release_event_line(self):
        txt = self.command('z')
        return

    def reset_DAQ_MCU(self):
        txt = self.command('R')
        return

    def flush_rx2_buffer(self):
        txt = self.command('F')
        return

    def test_DAQ_MCU_is_ready(self):
        txt = self.command('Q')
        event_txt, ready_txt = txt.split()
        return ready_txt == '1'

    def test_event_has_passed(self):
        txt = self.command('Q')
        event_txt, ready_txt = txt.split()
        return event_txt == '0'

    def set_VREF_on(self, level):
        '''
        Enable the analog-voltage output of the PIC MCU.
        level is an 8-bit integer 0-255.
        The output is set at (level/256 * 4.096) Volts.
        '''
        level = int(level)
        if level < 0: level = 0
        if level > 255: level = 255
        txt = self.command(f'w {level} 1')
        return

    def set_VREF_off(self):
        '''
        Disable the analog-voltage output of the PIC MCU.
        '''
        txt = self.command(f'w 0 0')
        return

    def enable_external_trigger(self, level, slope):
        '''
        Enable the external-trigger input to the PIC MCU.

        level is an 8-bit integer 0-255.
        The analog trigger is set at (level/256 * 4.096) Volts.

        With positive slope the EVENT# line is driven active-low
        when the external voltage exceeds the trigger level.
        With negative slope the EVENT# line is driven active-low
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
        txt = self.command(f'e {level} {slope}')
        if txt.find('error') >= 0:
            raise RuntimeError('Could not set external trigger.')
        return

    def disable_external_trigger(self):
        txt = self.command_PIC(f'd')
        return

    #---------------------------------------------------------------
    # DAQ-MCU interaction functions are implemented
    # by passing commands through the PIC18F16Q41 COMMS-MCU.

    def command_DAQ_MCU(self, cmd_txt):
        '''
        Wraps the cmd_txt as a pass-through-command and sends it.
        Returns the unwrapped response text.
        '''
        txt = self.command('X%s' % cmd_txt)
        if txt.find('ok') >= 0:
            txt = re.sub('ok', '', txt, count=1).strip()
        else:
            raise RuntimeError(f'DAQ_MCU response not ok: {txt}')
        return txt


if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 pic18f16q41_comms_1_mcu.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '1'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        node1 = PIC18F16Q41_COMMS_1_MCU(node_id, sp)
        print("Just some fiddling around to see that board is alive.")
        node1.set_LED(1)
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
        node1.set_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
