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

    def clear_data_array(self):
        # Clear the data[N_FULLWORDS] array to all zeros
        print(f"{ANSI_GREEN} RP2350 MCU > data cleared!{ANSI_RESET}")
        return self.comms_MCU.command_DAQ_MCU('0')
    
    def reset_registers(self):
        # Reset all registers to default values
        return self.comms_MCU.command_DAQ_MCU('F')
    
    def _set_register(self, reg, val):
        # Private: Set virtual register (0-6)
        return self.comms_MCU.command_DAQ_MCU(f's,{reg},{val}')
    
    def _get_register(self, reg):
        # Get virtual register value: 0=f_CLKIN(kHz), 1=OSR, 2=n_samples, 3=trig_mode,
        # 4=trig_ch, 5=trig_level, 6=trig_slope
        return self.comms_MCU.command_DAQ_MCU(f'r,{reg}')
    
    def set_clk(self, clk):
        # Set clock rate in kHz
        print(f"{ANSI_YELLOW} ADS131M04 > Setting clock to {clk} kHz{ANSI_RESET}")
        return self._set_register(0, clk)
    
    def set_osr(self, osr):
        # Set over-sampling ratio, auto-rounds to nearest valid: 128, 256, 512, 1024, 2048, 4096, 8192, 16256
        valid_osr = [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16256]
        # Find nearest valid OSR
        nearest = min(valid_osr, key=lambda x: abs(x - osr))
        # Let the user know what was chosen
        print(f"{ANSI_YELLOW} ADS131M04 > Selected OSR: {nearest}{ANSI_RESET}")
        # we're going to do a kSPS check, pull the clock rate from register 0
        clock_rate = float(self._get_register(0))
        print(f"{ANSI_YELLOW} ADS131M04 > Clock rate (kHz): {clock_rate}{ANSI_RESET}")
        # print the sample period in uS
        sample_period = (2000 * float(nearest)) / clock_rate # in microseconds
        kSPS = clock_rate / (2*float(nearest)) # ADS131M04 section 9.2.2.3
        print(f"{ANSI_YELLOW} ADS131M04 > Period (uS): {sample_period:.2f}, kSPS: {kSPS}{ANSI_RESET}")
        return self._set_register(1, nearest)
    
    def get_dt_us(self):
        # Get sample period in microseconds
        osr = float(self._get_register(1))
        clock_rate = float(self._get_register(0))
        sample_period = (2000 * osr) / clock_rate # in microseconds
        return sample_period

    def set_num_samples(self, n_samples):
        # Set number of samples in record after trigger event
        return self._set_register(2, n_samples)
    def get_num_samples(self):
        # Get number of samples in record after trigger event
        return int(self._get_register(2))
    
    def set_trigger_mode(self, mode=2):
        # Set trigger mode: 0=immediate, 1=internal, 2=external (default)
        return self._set_register(3, mode)
    def get_trigger_mode(self):
        # Get trigger mode
        val = self._get_register(3)
        if val == '0':
            return f"immediate"
        elif val == '1':
            return f"internal"
        elif val == '2':
            return f"external"
        else:
            return f"error"

    def set_trigger_channel(self, channel):
        # Set trigger channel for internal trigger (0-3)
        return self._set_register(4, channel)
    def get_trigger_channel(self):
        # Get trigger channel for internal trigger (0-3)
        return int(self._get_register(4))
    
    def set_trigger_level(self, level):
        # Set trigger level as signed integer
        return self._set_register(5, level)
    def get_trigger_level(self):
        # Get trigger level as signed integer
        return int(self._get_register(5))
    
    def set_trigger_slope(self, slope):
        # Set trigger slope: 0=sample-below-level, 1=sample-above-level
        return self._set_register(6, slope)
    def get_trigger_slope(self):
        # Get trigger slope
        val = self._get_register(6)
        if val == '0':
            return f"sample-below-level"
        elif val == '1':
            return f"sample-above-level"
        else:
            return f"error"
        
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
        eflag = self.comms_MCU.command_DAQ_MCU('k')
        print(f"{ANSI_GREEN} RP2350 MCU > ERROR FLAG: {eflag}{ANSI_RESET}")
        return eflag
    
    def sample(self):
        # Start sampling process
        return self.comms_MCU.command_DAQ_MCU('g')

    def enable_LED(self):
        return self.comms_MCU.command_DAQ_MCU('L,1')
    
    def disable_LED(self):
        return self.comms_MCU.command_DAQ_MCU('L,0')
    
    def release_pico2_event(self):
        return self.comms_MCU.command_DAQ_MCU('z')

    def get_trigger_index(self):
        # Get the sample index where the trigger occurred.
        # For circular buffer operation (TRIGGER_INTERNAL or TRIGGER_EXTERNAL modes),
        # this tells you which sample in the buffer corresponds to the trigger event.
        response = self.comms_MCU.command_DAQ_MCU('T')
        return int(response.strip())

    def get_oldest_sample_index(self):
        # Get the index of the oldest sample stored in SRAM.
        response = self.comms_MCU.command_DAQ_MCU('a')
        return int(response.strip())
    
    def get_formatted_sample(self, i):
        '''
        Returns the values of the recorded sample set i,
        where i is counted from the oldest recorded sample (i=0).

        The Pico2 reports these values as a string of space-separated integers.
        '''
        return [int(item) for item in self.comms_MCU.command_DAQ_MCU(f'P {i}').split()]

    def get_byte_sample(self, i):
        '''
        Returns the values of the recorded sample set i as int32 values,
        where i is counted from the oldest recorded sample (i=0).
        
        This method uses hex-encoded binary transfer ('B' command) which is more efficient
        than the decimal string-based 'P' command (~20% smaller), especially for large datasets.
        
        The Pico2 sends 32 hex characters (4 channels × 8 hex chars/channel) in little-endian format.
        Returns: list of 4 int32 values [ch0, ch1, ch2, ch3]
        '''
        response = self.comms_MCU.command_DAQ_MCU(f'B {i}')
        # Response format: "B " followed by 32 hex characters (8 per channel)
        # Remove any whitespace
        hex_data = response.strip()
        
        # Parse 4 int32 values from hex string (8 hex chars = 4 bytes each)
        samples = []
        for ch in range(4):
            # Extract 8 hex characters for this channel
            hex_str = hex_data[ch*8:(ch+1)*8]
            # Convert hex string to bytes (little-endian)
            byte_data = bytes.fromhex(hex_str)
            # Unpack as signed int32 (little-endian)
            value = struct.unpack('<i', byte_data)[0]
            samples.append(value)
        
        return samples

    #------------------------
    # Higher-level functions.
    #------------------------

    def fetch_SRAM_data(self, n_pretrigger=128):
        '''
        Returns a bytearray containing a selection of the SRAM data,
        along with enough metadata to interpret the bytes as samples.

        The number of samples is determined from the DAQ_MCU settings.
        If n_pretrigger is specified, that many samples before the trigger
        will be included (if available). Otherwise, default pretrigger samples is 128.
        '''
        nchan = 4  # number of ADS131M04 channels
        # Determine how many samples are stored in SRAM
        nsamples_after_trigger = self.get_num_samples()
        index_of_oldest_data = self.get_oldest_sample_index()
        first_sample_index = self.get_trigger_index()
        trigger_mode_str = self.get_trigger_mode()
        dt_us = self.get_dt_us()
        
        # Calculate the range of samples to fetch
        # For trigger modes with circular buffer, we want pre-trigger data
        if trigger_mode_str in ['internal', 'external']:
            # Get n_pretrigger samples before the trigger
            start_index = max(0, first_sample_index - n_pretrigger)
            total_samples = n_pretrigger + nsamples_after_trigger
        else:
            # For immediate mode, start from the beginning
            start_index = 0
            total_samples = nsamples_after_trigger
            n_pretrigger = 0  # No pre-trigger samples in immediate mode
        
        # Create bytearray to hold the data
        # Each sample has 4 channels × 4 bytes/channel = 16 bytes
        _ba = bytearray()
        
        # Fetch samples using the efficient hex-based get_byte_sample
        print(f"{ANSI_GREEN} RP2350 MCU > Fetching {total_samples} samples from SRAM...{ANSI_RESET}")
        for i in range(total_samples):
            # Print progress every 100 samples or on the last sample
            if i % 100 == 0 or i == total_samples - 1:
                percent = (i + 1) / total_samples * 100
                print(f"\r{ANSI_PINK} RP2350 MCU > Fetch progress: {i+1}/{total_samples} ({percent:.1f}%){ANSI_RESET}", end='', flush=True)
            
            sample_values = self.get_byte_sample(start_index + i)
            # Pack each int32 value as 4 bytes (little-endian) into the bytearray
            for value in sample_values:
                _ba.extend(struct.pack('<i', value))
        
        print()  # New line after progress is complete
        print(f"{ANSI_GREEN} RP2350 MCU > Fetch complete!{ANSI_RESET}")
        
        return {'index_of_oldest_data':index_of_oldest_data,
                'nsamples_after_trigger': nsamples_after_trigger,
                'nsamples_before_trigger': n_pretrigger,
                'first_sample_index': first_sample_index,
                'trigger_mode':trigger_mode_str,
                'nchan':nchan,
                'dt_us':dt_us,
                'data':_ba}

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