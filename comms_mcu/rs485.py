# rs485.py
# Functions to interact with the AVR64EA28+PIC18F16Q41 edaq node
# through a serial RS485 cable.
#
# PJ 2024-03-30: Begin with just getting version strings for both MCUs.
#    2024-04-01: Fill in more interaction functions, up to sampling.
#    2024-04-03: Functions to get SRAM data.
#    2024-04-18: Refactor to enable different DAC_MCU flavours.
#    2024-08-14: Add burst-mode sampling.
#    2025-10-20: Strip down to just the RS485 code.
#
import argparse
import serial
import time
import serial.tools.list_ports as list_ports
import re
import struct

# -----------------------------------------------------------------------------
# The RS485 communication happens through a standard serial port.
# Use pySerial to handle this connection.

def serial_ports():
    return [p.device for p in list_ports.comports()]

def openPort(port='/dev/ttyUSB0'):
    '''
    Returns a handle to the opened serial port, or None.
    '''
    ser = None
    try:
        ser = serial.Serial(port, 115200, rtscts=0, timeout=0.5)
    except serial.serialutil.SerialException:
        print(f'Did not find serial port: {port}')
        print(f'Serial ports that can be seen: {serial_ports()}')
        return None
    return ser

# -----------------------------------------------------------------------------
# Each data-recording node on the RS485 bus will be represented in this program
# by and instance of the following class.

class Node(object):
    __slots__ = ['id_char', 'serial_port']

    def __init__(self, id_char, serial_port):
        '''
        Each node on the RS485 bus should listen to all messages but
        accept and act only on the messages addressed to their id.

        The controlling node (master) has id character b'0'.
        Other nodes may be '1', '2', ... 'A' .. 'Z', 'a' .. 'z'.
        '''
        self.id_char = id_char
        self.serial_port = serial_port
        return

    #---------------------------------------------------------
    # Fundamentally, it's all messages on the RS485 bus.

    def send_command(self, cmd_txt):
        '''
        Send the wrapped command text on the RS485 bus to a specific COMMS-MCU.

        For notes, see PJ's workbook page 76, 2024-01-09.
        '''
        self.serial_port.reset_input_buffer()
        cmd_bytes = f'/{self.id_char}{cmd_txt}!\n'.encode('utf-8')
        # print("DEBUG cmd_bytes=", cmd_bytes)
        self.serial_port.write(cmd_bytes)
        self.serial_port.flush()
        return

    def get_response(self):
        '''
        Returns the unwrapped response text that comes back
        from a previously sent command.

        For notes, see PJ's workbook page 76, 2024-01-09.
        '''
        txt = self.serial_port.readline().strip().decode('utf-8')
        # print("DEBUG txt=", txt)
        if txt.startswith('/0'):
            if txt.find('#') < 0:
                print('Incomplete RS485 response:', txt)
            else:
                txt = re.sub('/0', '', txt).strip()
                txt = re.sub('#', '', txt).strip()
        else:
            raise RuntimeError(f'Invalid RS485 response: {txt}')
        return txt

    def command(self, cmd_txt):
        '''
        Sends the text of a command to the COMMS MCU.
        Returns the text of the RS485 return message.

        Each command to the COMMS MCU is encoded as the first character
        of the command text. Any required data follows that character.

        A return message should start with the same command character
        and may have more text following that character.
        A command that is not successful should send back a message
        with the word "error" in it, together with some more information.
        '''
        cmd_char = cmd_txt[0]
        self.send_command(cmd_txt)
        txt = self.get_response()
        if not txt.startswith(cmd_char):
            raise RuntimeError(f'Unexpected response: {txt}')
        txt = re.sub(cmd_char, '', txt, count=1).strip()
        if txt.find('error') >= 0:
            print("Warning: error return for command to COMMS-MCU.")
            print(f"  cmd_txt: {cmd_txt}")
            print(f"  response: {txt}")
        return txt


if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 rs485.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '1'
    if args.identity: node_id = args.identity
    sp = openPort(port_name)
    if sp:
        node1 = Node(node_id, sp)
        print("To see that board is alive, ask for its version string.")
        node1.send_command('v')
        txt = node1.get_response()
        print(f"response= {txt}")
    else:
        print("Did not find the serial port.")
    print("Done.")
