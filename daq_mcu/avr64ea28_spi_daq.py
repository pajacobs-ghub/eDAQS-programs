# avr64ea28_spi_daq.py
#
# Peter J.
# 2025-10-20: Adapted from avr64ea28_daq_mcu.py.
# 2025-10-26: Functions to control on-board LEDs.
#
import sys
sys.path.append("..")
from comms_mcu import rs485
from comms_mcu.pic18f16q41_spectrometer_comms import PIC18F16Q41_SPECTROMETER_COMMS
import struct

class AVR64EA28_SPI_DAQ(object):
    """
    DAC_MCU service functions for the 5 AVR64EA28 microcontrollers
    on the differential-spectrometer DAQ board.
    """

    __slots__ = ['comms_MCU', 'n_reg', 'reg_labels', 'reg_labels_to_int',
                 'ref_voltages', 'ref_voltages_int_to_value',
                 'pga_gains', 'pga_gains_int_to_value',
                 'sample_accumulation_number',
                 ]

    def __init__(self, comms_MCU):
        '''
        We do all of the interaction with the DAQ_MCU through the COMMS_MCU.
        '''
        self.comms_MCU = comms_MCU
        #
        # The following data should match the firmware programmed into the AVR.
        # A dictionary is used so that it is easy to cross-check the labels.
        self.n_reg = 6
        self.reg_labels = {
            0:'STATE', 1:'V_REF', 2:'PGA_FLAG', 3:'PGA_GAIN', 4:'NBURST', 5:'ALLOW_LED'
        }
        assert self.n_reg == len(self.reg_labels), "Oops, check reg_labels."
        self.reg_labels_to_int = {
            'STATE':0, 'V_REF':1, 'PGA_FLAG':2, 'PGA_GAIN':3, 'NBURST':4, 'ALLOW_LED':5
        }
        assert self.n_reg == len(self.reg_labels_to_int), "Oops, check reg_labels_to_int."
        self.pga_gains = {
            '1X':0, '1x':0, 1:0,
            '2X':1, '2x':1, 2:1,
            '4X':2, '4x':2, 4:2,
            '8X':3, '8x':3, 8:3,
            '16X':4, '16x':4, 16:4
        }
        self.pga_gains_int_to_value = {
            0:1,
            1:2,
            2:4,
            3:8,
            4:16
        }
        self.sample_accumulation_number = {
            # Actual samples per conversion is 2^^(this number).
            # Only a limited number of options are available,
            # as given in Table 31.5.10 of the data sheet.
            'NONE':0, 'none':0, 0:0,
            'ACC2':1, 'acc2':1, 2:1,
            'ACC4':2, 'acc4':2, 4:2,
            'ACC8':3, 'acc8':3, 8:3,
            'ACC16':4, 'acc16':4, 16:4,
            'ACC32':5, 'acc32':5, 32:5,
            'ACC64':6, 'acc64':6, 64:6,
            'ACC128':7, 'acc128':7, 128:7,
            'ACC256':8, 'acc256':8, 256:8,
            'ACC512':9, 'acc512':9, 512:9,
            'ACC1024':10, 'acc1024': 10, 1024:10
        }
        self.ref_voltages = {
            'VDD':0, 0:0,
            '1v024':1, '1.024':1, 1:1,
            '2v048':2, '2.048':2, 2:2,
            '4v096':3, '4.096':3, 3:3,
            '2v500':4, '2.500':4, 4:4,
        }
        self.ref_voltages_int_to_value = {
            0:4.75,  # Approximate value of Vsys after Schottky diode drop.
            1:1.024,
            2:2.048,
            3:4.096,
            4:2.500
        }
        return

    def get_version(self, iavr):
        '''
        Returns the string giving the version and date of the AVR firmware.
        '''
        mybytes = self.comms_MCU.command_DAQ_MCU(iavr, [124])
        mybytes = self.comms_MCU.command_DAQ_MCU(iavr, [0,]+20*[0,])
        # Discard the first 2 bytes because they were left in the AVR's SPI buffer
        # from a previous exchange.
        # Also, drop trailing null characters.
        mybytes = bytearray([b for b in mybytes[2:] if b != 0])
        return mybytes.decode('utf8')

    def get_register_bytes(self, iavr):
        '''
        Returns the byte values of the virtual-registers in a particular AVR MCU
        '''
        # First, send the command to put the vreg contents into the outgoing buffer.
        mybytes = self.comms_MCU.command_DAQ_MCU(iavr, [96])
        # Then, exchange sufficient bytes to fetch the data.
        mybytes = self.comms_MCU.command_DAQ_MCU(iavr, [0,]+10*[0,])
        # Discard the first 2 bytes because they were left in the AVR's SPI buffer
        # from a previous exchange.
        mybytes = bytearray([b for b in mybytes[2:2+self.n_reg]])
        return mybytes

    def get_registers_as_dict(self, iavr):
        '''
        Returns a dict representation of the all of the register byte values.
        '''
        mybytes = self.get_register_bytes(iavr)
        mydict = {}
        for i in range(len(mybytes)): mydict[self.reg_labels[i]] = mybytes[i]
        return mydict

    def halt_sampling(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [112, 0])
        return

    def resume_sampling(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [112, 1])
        return

    def set_PGA(self, iavr, gain='8X'):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [114, 1]) # via PGA
        self.comms_MCU.command_DAQ_MCU(iavr, [115, self.pga_gains[gain]])
        return

    def clear_PGA(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [114, 0]) # direct
        self.comms_MCU.command_DAQ_MCU(iavr, [115, 0]) # 1X
        return

    def set_ref_voltage(self, iavr, vStr):
        '''
        Select the reference voltage from a symbolic name.
        'VDD', '1v024', '2v048', '4v096', or '2v500'
        '''
        refVsel = self.ref_voltages['4v096']
        try:
            refVsel = self.ref_voltages[vStr]
        except:
            refVsel = self.ref_voltages['4v096']
        self.comms_MCU.command_DAQ_MCU(iavr, [113, refVsel])
        return

    def set_burst(self, iavr, n):
        '''
        The number of samples per conversion is 2**n.

        Note that when setting this number nonzero,
        we will get conversion results that are 16 times
        the nominal 12-bit value because we have elected
        to use burst-mode with result scaling.
        '''
        log2n = 0
        try:
            log2n = self.sample_accumulation_number[n]
        except:
            log2n = 0
        self.comms_MCU.command_DAQ_MCU(iavr, [116, log2n])
        return

    def suppress_LED(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [117, 0])
        return

    def allow_LED(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [117, 1])
        return

    def turn_off_LED(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [126,])
        return

    def turn_on_LED(self, iavr):
        '''
        '''
        self.comms_MCU.command_DAQ_MCU(iavr, [127,])
        return

    def get_sample_data(self, iavr):
        '''
        Returns a tuple containing the current analog values for a specific AVR.
        '''
        # First, send the command to put the data into the outgoing buffer.
        mybytes = self.comms_MCU.command_DAQ_MCU(iavr, [80])
        # Then, exchange sufficient bytes to fetch the data.
        mybytes = self.comms_MCU.command_DAQ_MCU(iavr, [0,]+18*[0,])
        # Discard the first 2 bytes because they were left in the AVR's SPI buffer
        # from a previous exchange.
        s = struct.Struct('>8h')
        values = s.unpack_from(mybytes, offset=2)
        return values

    def fetch_all_analog_samples(self):
        '''
        Issue the command to the PIC18 to gather up the analog data
        from all of the AVRs and return it as a single message.
        Returns the content of that message as a string.
        '''
        return self.comms_MCU.rs485_node.command('D')

if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 avr64ea28_spi_daq.py -i 2
    import argparse
    import time
    parser = argparse.ArgumentParser(description="AVR64EA28 SPI DAQ test program")
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
        print("First, some fiddling around to see that board is alive.")
        node1.set_LED(1)
        print(node1.get_version())
        avr = AVR64EA28_SPI_DAQ(node1)
        for i in range(5):
            print(f"For AVR {i}: version string = {avr.get_version(i)}")
            print(f"         : register bytes = {avr.get_register_bytes(i)}")
            print(f"         : initially = {avr.get_registers_as_dict(i)}")
            avr.set_ref_voltage(i, '1v024')
            avr.set_PGA(i, '4X')
            avr.set_burst(i, 'ACC16')
            print(f"         : with V_REF=1v024 and PGA=4X = {avr.get_registers_as_dict(i)}")
            print(f"         : analog values = {avr.get_sample_data(i)}")
        time.sleep(1.0)
        print("Suspend and then resume sampling.")
        for i in range(5): avr.halt_sampling(i)
        for i in range(5):
            time.sleep(0.5)
            avr.turn_on_LED(i)
            time.sleep(0.5)
            avr.turn_off_LED(i)
        time.sleep(1)
        for i in range(5): avr.resume_sampling(i)
        time.sleep(1)
        for i in range(5):
            print(f"For AVR {i}: analog values = {avr.get_sample_data(i)}")
        for i in range(3):
            print("All analog data=", avr.fetch_all_analog_samples())
        node1.set_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
