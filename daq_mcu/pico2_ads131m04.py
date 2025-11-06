# pico2_ads141m04.py
#
# Jeremy M.
# 2025-10-20: Adapted from avr64ea28_daq_mcu.py.
# 2025-10-26: Functions to control on-board LEDs.
# 2025-11-06: Modified for Jeremy's ADS141M04 board.

import sys
sys.path.append("..")
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
import struct

# ANSI color codes
ANSI_YELLOW = " \27[33m "
ANSI_GREEN  = " \27[32m "
ANSI_PINK  = " \27[35m "
ANSI_RESET = " \27[0m "

class PICO2_ADS131M04_DAQ(object):
    """
    DAC_MCU service functions for the Pico2 microcontroller
    connected to the ADS141M04 ADC. Specifically for Jeremy's SUPER-ADC boards.
    """

    __slots__ = ['comms_MCU']
    def __init__(self, comms_MCU):
        '''
        We do all of the interaction with the DAQ_MCU through the COMMS_MCU.
        '''
        self.comms_MCU = comms_MCU

    def get_version(self):
        """
        Gets the version string from the DAQ_MCU.
        """
        return self.comms_MCU.command_DAQ_MCU('v')

    def reset_registers(self):
        """
        Resets all ADS141M04 registers to default values.
        """
        return self.comms_MCU.command_DAQ_MCU('F')
    
    def single_sample(self):
        """
        Take a single sample from the ADS141M04 and return the raw data as a list of integers.
        """
        return self.comms_MCU.command_DAQ_MCU('I')
    
    def single_sample_as_ints(self):
        """
        Take a single sample and return as a list of 24-bit signed integers.
        Returns: [ch0, ch1, ch2, ch3]
        """
        result = self.single_sample()
        return [int(x) for x in result.split()]
    
    def single_sample_as_volts(self, vref=1.2, gain=1):
        """
        Take a single sample and convert to voltages.
        
        Args:
            vref: Reference voltage in volts (default 1.2V for internal reference)
            gain: PGA gain setting (default 1, can be 1, 2, 4, 8, 16, 32, 64, 128)
        
        Returns: List of voltages [ch0_v, ch1_v, ch2_v, ch3_v]
        
        Formula: Voltage = (ADC_Code / 2^23) * (VREF / Gain)
        where ADC_Code is 24-bit signed (-8388608 to +8388607)
        """
        adc_values = self.single_sample_as_ints()
        # ADS131M04 is 24-bit, so full scale is ±2^23
        full_scale = 2**23  # 8388608
        voltages = [(code / full_scale) * (vref / gain) for code in adc_values]
        return voltages
       
    def error_flags(self):
        """
        Get the current error flags from the ADS141M04.
        """
        return self.comms_MCU.command_DAQ_MCU('k')
    
    def sample(self):
        return self.comms_MCU.command_DAQ_MCU('g')

    def enable_LED(self):
        return self.comms_MCU.command_DAQ_MCU('L,1')
    
    def disable_LED(self):
        return self.comms_MCU.command_DAQ_MCU('L,0')

if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 avr64ea28_daq_mcu.py -i 2
    import argparse
    import time
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
        node1 = PIC18F16Q41_JM_ADS131M04_COMMS(node_id, sp)
        print("Just some fiddling around to see that board is alive.")
        node1.set_LED(1)
        print(node1.get_version())
        # If we have been reprogramming the DAQ_MCU while the PIC18 is running,
        # we will likely have rubbish characters in the PIC18's RX2 buffer.
        if not node1.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node1.reset_DAQ_MCU()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        daq_mcu = PICO2_ADS131M04_DAQ(node1)
        print(daq_mcu.get_version())


        time.sleep(1.0)
        node1.set_LED(0)
        for i in range(2):
            time.sleep(0.5)
            node1.set_LED(1)
            time.sleep(0.5)
            node1.set_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")