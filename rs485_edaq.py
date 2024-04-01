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
    __slots__ = ['id_char', 'serial_port', 'n_reg', 'reg_labels']

    def __init__(self, id_char, serial_port):
        '''
        Each node on the RS485 bus should listen to all messages but
        accept and act only on the messages addressed to their id.

        The controlling node (master) has id character b'0'.
        Other nodes may be '1', '2', ... 'A' .. 'Z', 'a' .. 'z'.
        '''
        self.id_char = id_char
        self.serial_port = serial_port
        # The following data should match the firmeare programmed into the AVR.
        # A dictionary is used so that it is easy to cross-check the labels.
        self.n_reg = 34
        self.reg_labels = {
            0:'PER_TICKS', 1:'NCHANNELS', 2:'NSAMPLES',
            3:'TRIG_MODE', 4:'TRIG_CHAN', 5:'TRIG_LEVEL', 6:'TRIG_SLOPE',
            7:'PGA_FLAG', 8:'PGA_GAIN', 9:'V_REF',
            10:'CH0+', 11:'CH0-', 12:'CH1+', 13:'CH1-', 14:'CH2+', 15:'CH2-',
            16:'CH3+', 17:'CH3-', 18:'CH4+', 19:'CH4-', 20:'CH5+', 21:'CH5-',
            22:'CH6+', 23:'CH6-', 24:'CH7+', 25:'CH7-', 26:'CH8+', 27:'CH8-',
            28:'CH9+', 29:'CH9-', 30:'CH10+', 31:'CH10-', 32:'CH11+', 33:'CH11-'
        }
        assert self.n_reg == len(self.reg_labels), "Oops, check register labels."
        return

    def send_RS485_command(self, cmd_txt):
        '''
        Send the wrapped command text on the RS485 bus.
        '''
        self.serial_port.reset_input_buffer()
        cmd_bytes = f'/{self.id_char}{cmd_txt}!\r'.encode('utf-8')
        # print("cmd_bytes=", cmd_bytes)
        self.serial_port.write(cmd_bytes)
        self.serial_port.flush()
        return

    def get_RS485_response(self):
        '''
        Returns the unwrapped response text that comes back
        from a previously sent command.
        '''
        txt = self.serial_port.readline().strip().decode('utf-8')
        if txt.startswith('/0'):
            if txt.find('#') < 0:
                print('Incomplete RS485 response:', txt)
            else:
                txt = re.sub('/0', '', txt).strip()
                txt = re.sub('#', '', txt).strip()
        else:
            raise(f'Invalid RS485 response: {txt}')
        return txt

    def command_PIC(self, cmd_txt):
        cmd_char = cmd_txt[0]
        self.send_RS485_command(cmd_txt)
        txt = self.get_RS485_response()
        if not txt.startswith(cmd_char):
            raise(f'Unexpected response: {txt}')
        txt = re.sub(cmd_char, '', txt).strip()
        return txt

    def get_PIC_version(self):
        return self.command_PIC('v')

    def command_AVR(self, cmd_txt):
        '''
        Wraps the cmd_txt as a pass-through-command and sends it.
        Returns the unwrapped response text.
        '''
        txt = self.command_PIC('X%s' % cmd_txt)
        if txt.find('ok'):
            txt = re.sub('ok', '', txt).strip()
        else:
            raise(f'AVR response not ok: {txt}')
        return txt

    def get_AVR_version(self):
        return self.command_AVR('v')

    def get_AVR_reg(self, i):
        '''
        Returns the value of the i-th pseudo-register.
        '''
        txt = self.command_AVR(f'r {i}')
        return int(txt)

    def set_AVR_reg(self, i, val):
        '''
        Sets the value of the i-th pseudo-register and
        returns the value reported.
        '''
        txt = self.command_AVR(f's {i} {val}')
        return int(txt.split()[1])

    def set_AVR_regs_from_dict(self, d):
        '''
        Set a number of AVR registers from values in a dictionary.

        This should be convenient form for defining configurations.
        '''
        for i in d.keys():
            val = d[i]
            print(f'Setting reg[{i}]={val} ({self.reg_labels[i]})')
            self.set_AVR_reg(i, val)
        return

    def print_AVR_reg_values(self):
        '''
        '''
        print('Reg  Val  Label')
        for i in range(self.n_reg):
            val = self.get_AVR_reg(i)
            print(i, val, self.reg_labels[i])
        return

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        print(node1.get_PIC_version())
        print(node1.get_AVR_version())
        print(node1.get_AVR_reg(0))
        print(node1.set_AVR_reg(0, 1250))
        print(node1.get_AVR_reg(0))
        node1.set_AVR_regs_from_dict({1:6, 2:100})
        node1.print_AVR_reg_values()

