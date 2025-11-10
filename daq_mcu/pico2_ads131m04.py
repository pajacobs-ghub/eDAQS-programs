# pico2_ads141m04.py
# Jeremy M. 2025-10-20: Adapted from avr64ea28_daq_mcu.py.

import sys
sys.path.append("..")
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
import struct
import time

# ANSI color codes
ANSI_YELLOW = "\033[33m"
ANSI_GREEN  = "\033[32m"
ANSI_PINK   = "\033[35m"
ANSI_RESET  = "\033[0m"

class PICO2_ADS131M04_DAQ(object):
    # DAQ_MCU service functions for Pico2 with ADS131M04 ADC
    __slots__ = ['comms_MCU']
    
    def __init__(self, comms_MCU):
        # All interaction with DAQ_MCU goes through COMMS_MCU
        self.comms_MCU = comms_MCU

    def get_version(self):
        # Get version string from DAQ_MCU
        return self.comms_MCU.command_DAQ_MCU('v')

    def reset_registers(self):
        # Reset all registers to default values
        return self.comms_MCU.command_DAQ_MCU('F')
    
    def _set_register(self, reg, val):
        # Private: Set virtual register (0-6)
        return self.comms_MCU.command_DAQ_MCU(f's,{reg},{val}')
    
    def get_register(self, reg):
        # Get virtual register value: 0=f_CLKIN(kHz), 1=OSR, 2=n_samples, 3=trig_mode,
        # 4=trig_ch, 5=trig_level, 6=trig_slope
        return self.comms_MCU.command_DAQ_MCU(f'r,{reg}')
    
    # Public setter functions
    def set_clk(self, clk):
        # Set clock rate in kHz
        return self._set_register(0, clk)
    def set_osr(self, osr):
        # Set over-sampling ratio, auto-rounds to nearest valid: 128, 256, 512, 1024, 2048, 4096, 8192, 16256
        valid_osr = [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16256]
        # Find nearest valid OSR
        nearest = min(valid_osr, key=lambda x: abs(x - osr))
        # Let the user know what was chosen
        print(f"{ANSI_YELLOW}Selected OSR: {nearest}{ANSI_RESET}")
        # we're going to do a kSPS check, pull the clock rate from register 0
        clock_rate = float(self.get_register(0))
        print(f"{ANSI_PINK}Clock rate (kHz): {clock_rate}{ANSI_RESET}")
        # print the sample period in uS
        sample_period = (2000 * float(nearest)) / clock_rate # in microseconds
        kSPS = clock_rate / (2*float(nearest)) # ADS131M04 section 9.2.2.3
        print(f"{ANSI_GREEN}Period (uS): {sample_period:.2f}, kSPS: {kSPS}{ANSI_RESET}")
        return self._set_register(1, nearest)
    
    def set_num_samples(self, n_samples):
        # Set number of samples in record after trigger event
        return self._set_register(2, n_samples)
    
    def set_trigger_mode(self, mode):
        # Set trigger mode: 0=immediate, 1=internal, 2=external (default)
        return self._set_register(2, mode)
    
    def set_trigger_channel(self, channel):
        # Set trigger channel for internal trigger (0-3)
        return self._set_register(4, channel)
    
    def set_trigger_level(self, level):
        # Set trigger level as signed integer
        return self._set_register(5, level)
    
    def set_trigger_slope(self, slope):
        # Set trigger slope: 0=sample-below-level, 1=sample-above-level
        return self._set_register(6, slope)
    
    def single_sample(self):
        # Take single sample, return raw data string
        return self.comms_MCU.command_DAQ_MCU('I')
    
    def single_sample_as_ints(self):
        # Take single sample, return [ch0, ch1, ch2, ch3] as ints
        result = self.single_sample()
        return [int(x) for x in result.split()]
    
    def single_sample_as_volts(self):
        # Convert sample to voltages: V = (code/2^23) * (vref/gain)
        vref = 1.2  # Default internal reference
        gain = 1    # Default PGA gain
        adc_values = self.single_sample_as_ints()
        full_scale = 2**23  # 24-bit ADC
        voltages = [(code / full_scale) * (vref / gain) for code in adc_values]
        return voltages
       
    def error_flags(self):
        # Get current error flags
        return self.comms_MCU.command_DAQ_MCU('k')
    
    def sample(self):
        # Start sampling process
        return self.comms_MCU.command_DAQ_MCU('g')

    def enable_LED(self):
        return self.comms_MCU.command_DAQ_MCU('L,1')
    
    def disable_LED(self):
        return self.comms_MCU.command_DAQ_MCU('L,0')

if __name__ == '__main__':
    # Basic test: python3 pico2_ads131m04.py -p /dev/ttyUSB0 -i 1
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
        print("Testing board connection...")
        node1.set_LED(1)
        print(node1.get_version())
        # Reset DAQ_MCU if needed (e.g., after reprogramming)
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