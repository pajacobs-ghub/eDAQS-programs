# pic18f16q41_spectrometer_comms.py
#
# Peter J.
# 2025-10-21: Adapted from pic18f16q41_comms_1_mcu code.
#
import argparse
import time
import re
import struct

import sys
sys.path.append("..")
from comms_mcu import rs485

class PIC18F16Q41_SPECTROMETER_COMMS(object):
    """
    COMMS-MCU service functions are built on RS485 messages.
    """

    __slots__ = ['rs485_node']

    def __init__(self, id_char, serial_port):
        self.rs485_node = rs485.Node(id_char, serial_port)
        return

    def get_version(self):
        return self.rs485_node.command('v')

    def suppress_LED(self):
        return self.rs485_node.command('s')

    def allow_LED(self):
        return self.rs485_node.command('a')

    def set_LED(self, val):
        txt = self.rs485_node.command(f'L{val}')
        return

    def reset_DAQ_MCUs(self):
        """
        Sends command to reset all 5 AVR MCUs.
        """
        txt = self.rs485_node.command('R')
        return

    def command_DAQ_MCU(self, avr_id, cmd_bytes):
        '''
        Wraps the cmd_byte array as a pass-through text command
        and sends it to a specific AVR MCU via the COMMS MCU.

        Returns the response bytes from the previous command
        to that specific AVR MCU.

        Because we are using buffered input at the AVR SPI module,
        the first two bytes returned in the exchange were pushed into
        the SPI registers on a previous exchange and should be discarded.
        This also means that we should exchange 2 more bytes than the
        number of significant bytes that we want.
        '''
        cmd_txt = ''
        for i in cmd_bytes: cmd_txt += (' %d' % i)
        txt = self.rs485_node.command('X %d %s' % (avr_id, cmd_txt))
        # print('DEBUG txt=', txt)
        response_bytes = bytearray([int(item, 16) for item in txt.strip().split()])
        return response_bytes


if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 pic18f16q41_spectrometer_comms.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'D'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        node1 = PIC18F16Q41_SPECTROMETER_COMMS(node_id, sp)
        print("Just some fiddling around to see that board is alive.")
        node1.set_LED(1)
        print(node1.get_version())
        for i in range(5):
            print(f"For AVR {i}:")
            mybytes = node1.command_DAQ_MCU(i, [124])
            print("cmd response A=", mybytes)
            mybytes = node1.command_DAQ_MCU(i, [0,]+20*[0,])
            print("cmd response B=", mybytes)
        time.sleep(1.0)
        node1.set_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
