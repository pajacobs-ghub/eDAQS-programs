# rs485_edaq.py
# Functions to interact with the AVR64EA28+PIC18F16Q41 edaq node
# through a serial RS485 cable.
#
# PJ 2023-03-30: Begin with just getting version strings for both MCUs.
#
import argparse
import serial
import time
import serial.tools.list_ports as list_ports
import re

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

class EDAQSNode(object):
    __slots__ = ['id_char', 'sp']

    def __init__(self, id_char, serial_port):
        '''
        Each node on the RS485 bus should listen to all messages but
        accept and act only on the messages addressed to their id.

        The controlling node (master) has id character b'0'.
        Other nodes may be '1', '2', ... 'A' .. 'Z', 'a' .. 'z'.
        '''
        self.id_char = id_char
        self.sp = serial_port
        return

    def send_RS485_command(self, cmd_txt):
        '''
        Send the wrapped command text on the RS485 bus.
        '''
        self.sp.reset_input_buffer()
        cmd_bytes = f'/{self.id_char}{cmd_txt}!\r'.encode('utf-8')
        # print("cmd_bytes=", cmd_bytes)
        self.sp.write(cmd_bytes)
        self.sp.flush()
        return

    def get_RS485_response(self):
        '''
        Returns the unwrapped response text that comes back
        from a previously sent command.
        '''
        txt = self.sp.readline().strip().decode('utf-8')
        if txt.startswith('/0'):
            if txt.find('#') < 0:
                print("Incomplete RS485 response:", txt)
            else:
                txt = re.sub('/0', '', txt).strip()
                txt = re.sub('#', '', txt).strip()
        else:
            print("Invalid RS485 response:", txt)
        return txt

    def get_PIC_version(self):
        self.send_RS485_command('v')
        return self.get_RS485_response()

    def get_AVR_version(self):
        self.send_RS485_command('Xv')
        txt = self.get_RS485_response()
        if txt.find('ok'):
            txt = re.sub('X', '', txt).strip()
            txt = re.sub('ok', '', txt).strip()
        else:
            print("AVR response not ok: ", txt)
        return txt

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        print(node1.get_PIC_version())
        print(node1.get_AVR_version())

