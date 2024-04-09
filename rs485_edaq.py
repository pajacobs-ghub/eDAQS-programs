# rs485_edaq.py
# Functions to interact with the AVR64EA28+PIC18F16Q41 edaq node
# through a serial RS485 cable.
#
# PJ 2024-03-30: Begin with just getting version strings for both MCUs.
#    2024-04-01: Fill in more interaction functions, up to sampling.
#    2024-04-03: Functions to get SRAM data.
#
import argparse
import serial
import time
import serial.tools.list_ports as list_ports
import re

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

class EDAQSNode(object):
    __slots__ = ['id_char', 'serial_port', 'n_reg', 'reg_labels',
                 'pins', 'channels', 'pga_gains',
                 'trigger_modes', 'trigger_slopes', 'us_per_tick']

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
        # Give names to the analog-in pins to make it easy to specify analog inputs.
        self.pins = {
            'AIN28':28, 'PC0':28, 28:28,
            'AIN29':29, 'PC1':29, 29:29,
            'AIN30':30, 'PC2':30, 30:30,
            'AIN31':31, 'PC3':30, 31:31,
            'AIN0':0, 'PD0':0, 0:0,
            'AIN1':1, 'PD1':1, 1:1,
            'AIN2':2, 'PD2':2, 2:2,
            'AIN3':3, 'PD3':3, 3:3,
            'AIN4':4, 'PD4':4, 4:4,
            'AIN5':5, 'PD5':5, 5:5,
            'AIN6':6, 'PD6':6, 6:6,
            'AIN7':7, 'PD2':7, 7:7,
            'GND':48
        }
        self.channels = []
        self.pga_gains = {
            '1X':0, '1x':0, 1:0,
            '2X':1, '2x':1, 2:1,
            '4X':2, '4x':2, 4:2,
            '8X':3, '8x':3, 8:3,
            '16X':4, '16x':4, 16:4,
        }
        self.trigger_modes = {
            'IMMEDIATE':0, 0:0,
            'INTERNAL':1, 1:1,
            'EXTERNAL':2, 2:2
        }
        self.trigger_slopes = {
            'NEG':0, 'BELOW':0, 0:0,
            'POS':1, 'ABOVE':1, 1:1
        }
        self.us_per_tick = 0.8 # Hardware timer set at this value.
        return

    #---------------------------------------------------------
    # Fundamentally, it's all messages on the RS485 bus.

    def send_RS485_command(self, cmd_txt):
        '''
        Send the wrapped command text on the RS485 bus.

        For notes, see PJ's workbook page 76, 2024-01-09.
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

        For notes, see PJ's workbook page 76, 2024-01-09.
        '''
        txt = self.serial_port.readline().strip().decode('utf-8')
        if txt.startswith('/0'):
            if txt.find('#') < 0:
                print('Incomplete RS485 response:', txt)
            else:
                txt = re.sub('/0', '', txt).strip()
                txt = re.sub('#', '', txt).strip()
        else:
            raise RuntimeError(f'Invalid RS485 response: {txt}')
        return txt

    #-----------------------------------------------------------
    # PIC18F16Q41 service functions are built on RS485 messages.

    def command_PIC(self, cmd_txt):
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
        self.send_RS485_command(cmd_txt)
        txt = self.get_RS485_response()
        if not txt.startswith(cmd_char):
            raise RuntimeError(f'Unexpected response: {txt}')
        txt = re.sub(cmd_char, '', txt, count=1).strip()
        if txt.find('error') >= 0:
            print("Warning: error return for command to PIC MCU.")
            print(f"  cmd_txt: {cmd_txt}")
            print(f"  response: {txt}")
        return txt

    def get_PIC_version(self):
        return self.command_PIC('v')

    def set_PIC_LED(self, val):
        txt = self.command_PIC(f'L{val}')
        return

    def assert_event_line_low(self):
        txt = self.command_PIC('t')
        return

    def release_event_line(self):
        txt = self.command_PIC('c')
        return

    def reset_AVR(self):
        txt = self.command_PIC('R')
        return

    def flush_rx2_buffer(self):
        txt = self.command_PIC('F')
        return

    def test_AVR_is_ready(self):
        txt = self.command_PIC('Q')
        event_txt, ready_txt = txt.split()
        return ready_txt == '1'

    def test_event_has_passed(self):
        txt = self.command_PIC('Q')
        event_txt, ready_txt = txt.split()
        return event_txt == '0'

    def set_PIC_VREF_on(self, level):
        '''
        Enable the analog-voltage output of the PIC MCU.
        level is an 8-bit integer 0-255.
        The output is set at (level/256 * 4.096) Volts.
        '''
        level = int(level)
        if level < 0: level = 0
        if level > 255: level = 255
        txt = self.command_PIC(f'w {level} 1')
        return

    def set_PIC_VREF_off(self):
        '''
        Disable the analog-voltage output of the PIC MCU.
        '''
        txt = self.command_PIC(f'w 0 0')
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
        txt = self.command_PIC(f'e {level} {slope}')
        if txt.find('error') >= 0:
            raise RuntimeError('Could not set external trigger.')
        return

    def disable_external_trigger(self):
        txt = self.command_PIC(f'd')
        return

    #---------------------------------------------------------------
    # AVR DAQ-MCU interaction functions are implemented
    # by passing commands through the PIC18F16Q41 COMMS-MCU.

    def command_AVR(self, cmd_txt):
        '''
        Wraps the cmd_txt as a pass-through-command and sends it.
        Returns the unwrapped response text.
        '''
        txt = self.command_PIC('X%s' % cmd_txt)
        if txt.find('ok') >= 0:
            txt = re.sub('ok', '', txt, count=1).strip()
        else:
            raise RuntimeError(f'AVR response not ok: {txt}')
        return txt

    #----------------------------------------------------------------
    # AVR service functions.

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

    def set_AVR_regs_to_factory_values(self):
        txt = self.command_AVR('F')
        return

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

    def set_AVR_sample_period_us(self, dt_us):
        '''
        '''
        ticks = int(dt_us / self.us_per_tick)
        # [TODO] should put some checks on this.
        self.set_AVR_reg(0, ticks)
        return

    def set_AVR_analog_channels(self, chan_list):
        '''
        Set the channel registers from a list of input-pin tuples.

        Each tuple names the positive and negative inputs.
        '''
        self.channels = []
        for pos,neg in chan_list:
            if len(self.channels) == 12: break
            if type(pos) is str: pos = pos.upper()
            if type(neg) is str: neg = neg.upper()
            self.channels.append((self.pins[pos], self.pins[neg]))
        nchan = len(self.channels)
        self.set_AVR_reg(1, nchan)
        for i in range(nchan):
            self.set_AVR_reg(10+i*2, self.channels[i][0])
            self.set_AVR_reg(11+i*2, self.channels[i][1])
        return

    def set_AVR_PGA(self, gain='8X'):
        '''
        '''
        self.set_AVR_reg(7, 1) # via PGA
        self.set_AVR_reg(8, self.pga_gains[gain])
        return

    def clear_AVR_PGA(self):
        '''
        '''
        self.set_AVR_reg(7, 0) # direct
        self.set_AVR_reg(8, 0) # 1X
        return

    def immediate_AVR_sample_set(self):
        '''
        '''
        txt = self.command_AVR('I')
        return txt

    def set_AVR_trigger_immediate(self):
        '''
        Set the trigger mode to IMMEDIATE.

        Recording will start immediately that the MCU is told to start sampling
        and will stop after nsamples have been recorded.
        '''
        self.set_AVR_reg(3, self.trigger_modes['IMMEDIATE'])
        return

    def set_AVR_trigger_internal(self, chan, level, slope):
        '''
        Set the trigger mode to INTERNAL.

        Recording will start immediately that the MCU is told to start sampling
        and will continue indefinitely, until the specified channel crosses
        the specified level.
        nsamples with then be recorded and the sampling stops after than.
        '''
        # [TODO] some checking for reasonable input.
        self.set_AVR_reg(3, self.trigger_modes['INTERNAL'])
        self.set_AVR_reg(4, chan)
        self.set_AVR-reg(5, level)
        self.set_AVR_reg(6, self.trigger_slopes[slope])
        return

    def set_AVR_trigger_external(self):
        '''
        Set the trigger mode to EXTERNAL.

        Recording will start immediately that the MCU is told to start sampling
        and will continue indefinitely, until the EVENT# pin goes low.
        nsamples with then be recorded and the sampling stops after than.
        '''
        self.set_AVR_reg(3, self.trigger_modes['EXTERNAL'])
        return

    def set_AVR_nsamples(self, n):
        '''
        Set the number of samples to be recorded after trigger event.
        '''
        # [TODO] some checking for reasonable input.
        self.set_AVR_reg(2, n)
        return

    def start_AVR_sampling(self):
        '''
        Start the AVR sampling.

        What happens from this point depends on the register settings
        and, maybe, the external signals.
        '''
        self.command_AVR('g')
        return

    def get_AVR_nchannels(self):
        return self.get_AVR_reg(1)

    def get_AVR_byte_size_of_sample_set(self):
        return int(self.command_AVR('b'))

    def get_AVR_max_nsamples(self):
        return int(self.command_AVR('m'))

    def get_AVR_size_of_SRAM_in_bytes(self):
        return int(self.command_AVR('T'))

    def get_AVR_nsamples(self):
        return self.get_AVR_reg(2)

    def get_AVR_trigger_mode(self):
        return self.get_AVR_reg(3)

    def get_AVR_formatted_sample(self, i):
        return [int(item) for item in self.command_AVR(f'P {i}').split()]

    def get_recorded_data(self):
        '''
        Returns a list of lists containing the recorded values for each channel.
        '''
        nchan = self.get_AVR_nchannels()
        _data = [[] for c in range(nchan)]
        #
        nsamples = self.get_AVR_nsamples()
        max_samples = self.get_AVR_max_nsamples()
        mode = self.get_AVR_trigger_mode()
        N = nsamples if mode==0 else max_samples
        for i in range(N):
            sample_values = self.get_AVR_formatted_sample(i)
            for j in range(nchan): _data[j].append(sample_values[j])
        return _data

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Just some fiddling around to see that board is alive.")
        node1.set_PIC_LED(1)
        print(node1.get_PIC_version())
        # If we have been reprogramming the AVR while the PIC18 is running,
        # we will likely have rubbish characters in the PIC18's RX2 buffer.
        if not node1.test_AVR_is_ready():
            print("Reset AVR")
            node1.reset_AVR()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        print(node1.get_AVR_version())
    else:
        print("Did not find the serial port.")
    print("Done.")
