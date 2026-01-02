# pico2_daq_mcu_bu79100g.py
#
# Peter J.
# 2025-11-09: Adapted from avr64ea28_daq_mcu.py but not yet ready for use.
# 2025-11-15: Clean up and put to first use.
# 2026-01-02: Accommodate the RTDP implementation.
#
import sys
sys.path.append("..")
from comms_mcu import rs485
from comms_mcu.pic18f26q71_comms_3_mcu import PIC18F26Q71_COMMS_3_MCU
import struct

class PICO2_DAQ_MCU_BU79100G(object):
    """
    DAC_MCU service functions for a Pico2 microcontroller driving 8 BU79100G ADCs.
    """

    __slots__ = ['comms_MCU',
                 'n_reg', 'reg_labels', 'reg_labels_to_int',
                 'trigger_modes', 'trigger_modes_int_to_sym']

    def __init__(self, comms_MCU):
        '''
        We do all of the interaction with the DAQ_MCU through the COMMS_MCU.
        '''
        self.comms_MCU = comms_MCU
        #
        # The following data should match the firmware programmed into the AVR.
        # A dictionary is used so that it is easy to cross-check the labels.
        self.n_reg = 5
        self.reg_labels = {
            0:'PERIOD_US',
            1:'NCHANNELS',
            2:'NSAMPLES',
            3:'TRIG_MODE',
            4:'RTDP_US'
        }
        assert self.n_reg == len(self.reg_labels), "Oops, check reg_labels."
        self.reg_labels_to_int = {
            'PERIOD_US':0,
            'NCHANNELS':1,
            'NSAMPLES':2,
            'TRIG_MODE':3,
            'RTDP_US': 4
        }
        assert self.n_reg == len(self.reg_labels_to_int), "Oops, check reg_labels_to_int."
        self.trigger_modes = {
            'IMMEDIATE':0, 0:0,
            'WAIT_FOR_EVENTn':1, 1:1
        }
        self.trigger_modes_int_to_sym = {
            0:'IMMEDIATE',
            1:'WAIT_FOR_EVENTn'
        }
        return

    def get_version(self):
        return self.comms_MCU.command_DAQ_MCU('v')

    def get_n_reg_actual(self):
        '''
        Get the actual number of virtual registers in the Pico2 DAQ MCU.
        This may be differ with firmware version.
        '''
        txt = self.comms_MCU.command_DAQ_MCU('n')
        return int(txt)

    def get_reg(self, i):
        '''
        Returns the value of the i-th vertual-register.
        '''
        n_reg_actual = self.get_n_reg_actual()
        if i >= n_reg_actual:
            raise RuntimeError(f'Requested register {i} but n_reg_actual is {n_reg_actual}.')
        txt = self.comms_MCU.command_DAQ_MCU(f'r {i}')
        return int(txt)

    def set_reg(self, i, val):
        '''
        Sets the value of the i-th virtual-register and
        returns the value reported.
        '''
        n_reg_actual = self.get_n_reg_actual()
        if i >= n_reg_actual:
            raise RuntimeError(f'Setting register {i} but n_reg_actual is {n_reg_actual}.')
        txt = self.comms_MCU.command_DAQ_MCU(f's {i} {val}')
        return int(txt.split()[1])

    def set_regs_to_factory_values(self):
        txt = self.comms_MCU.command_DAQ_MCU('F')
        return

    def set_regs_from_dict(self, d):
        '''
        Set a number of Pico2 virtual registers from values in a dictionary.

        This should be convenient form for defining configurations.
        '''
        n_reg_actual = self.get_n_reg_actual()
        for i in d.keys():
            val = d[i]
            if i >= n_reg_actual:
                raise RuntimeError(f'Setting register {i} but n_reg_actual is {n_reg_actual}.')
            print(f'Setting reg[{i}]={val} ({self.reg_labels[i]})')
            self.set_reg(i, val)
        return

    def get_reg_values_as_text(self):
        '''
        Returns a text representation of the all of the register values.
        '''
        n_reg_actual = self.get_n_reg_actual()
        txt = 'Reg  Val  Label\n'
        for i in range(n_reg_actual):
            val = self.get_reg(i)
            txt += f'{i} {val} {self.reg_labels[i]}\n'
        return txt

    def set_sample_period_us(self, dt_us):
        '''
        Sets the timer ticks register to achieve the sample period in microseconds.

        On the Pico2, the general timer is used and it ticks over with a microsecond period.
        '''
        ticks = int(dt_us)
        # [TODO] should put some checks on this.
        self.set_reg(0, ticks)
        return

    def get_sample_period_us(self):
        '''
        Returns sample period in microseconds.
        '''
        return self.get_reg(0)

    def set_RTDP_timeout_us(self, dt_us):
        '''
        Sets the RTDP timeout period in microseconds.

        A non-zero period will activate the RTDP.
        Note that the sample period needs to be >= 2 microseconds
        for the RTDP to be active.
        '''
        ticks = int(dt_us)
        # [TODO] should put some checks on this.
        self.set_reg(4, ticks)
        return

    def immediate_sample_set(self):
        '''
        Starts the main sampling process, but just for two sample cycles.

        Returns the data for the second cycle because the first cycle is
        likely to produce invalid data.
        '''
        txt = self.comms_MCU.command_DAQ_MCU('I')
        return txt

    def analog_millivolts(self):
        '''
        Returns the analog voltage (driving the BU79100G ADCs)
        in millivolts, as an integer.
        '''
        return self.comms_MCU.analog_millivolts()

    def get_trigger_mode(self):
        '''
        Returns the integer value representing the trigger mode.
        '''
        return self.get_reg(3)

    def set_trigger_immediate(self):
        '''
        Set the trigger mode to IMMEDIATE.

        Recording will start immediately that the MCU is told to start sampling
        and will stop after nsamples have been recorded.
        '''
        self.set_reg(3, self.trigger_modes['IMMEDIATE'])
        return

    def set_trigger_wait_for_eventn(self):
        '''
        Set the trigger mode to WAIT_FOR_EVENTn.

        Recording will start immediately that the MCU is told to start sampling
        and will continue indefinitely, until the EVENTn line goes low.
        nsamples with then be recorded and the sampling stops after.
        '''
        # [TODO] some checking for reasonable input.
        self.set_reg(3, self.trigger_modes['WAIT_FOR_EVENTn'])
        return

    def set_nsamples(self, n):
        '''
        Set the number of samples to be recorded after trigger event.
        '''
        # [TODO] some checking for reasonable input.
        if n < 0: n = 100 # Somewhat arbitrary.
        # The Pico2 retains only 16k sample sets.
        if n > 32768: n = 32768
        self.set_reg(2, n)
        return

    def start_sampling(self):
        '''
        Start the Pico2 sampling.

        What happens from this point depends on the register settings
        and, maybe, the external signals.
        '''
        self.comms_MCU.command_DAQ_MCU('g')
        return

    def did_not_keep_up_during_sampling(self):
        '''
        Returns a boolean flag indicating whether the requested sample period
        was always maintained.

        It takes only one late arrival at the end of the sampling loop to
        indicate that the Pico2 did not kep up during sampling.
        '''
        return (int(self.comms_MCU.command_DAQ_MCU('k')) == 1)

    def get_nchannels(self):
        '''
        Returns the number of channels that were recorded per sample set.
        '''
        return self.get_reg(1)

    def get_byte_size_of_sample_set(self):
        '''
        Returns the number of bytes used to store one sample set.

        Depends upon the number of channels being recorded.
        '''
        return int(self.comms_MCU.command_DAQ_MCU('b'))

    def get_max_nsamples(self):
        '''
        Returns the number of sample sets that can be stored in SRAM.

        This value is dependent on the amount of SRAM assigned to data storage
        and the number of channels being recorded.
        '''
        return int(self.comms_MCU.command_DAQ_MCU('m'))

    def get_size_of_SRAM_in_bytes(self):
        return int(self.comms_MCU.command_DAQ_MCU('T'))

    def get_byte_address_of_oldest_data(self):
        '''
        Returns the byte-address.

        Since the SRAM memory is treated as a circular buffer,
        this address may be almost anywhere in the available range.
        The possible sizes of each sample set is restricted
        so that sample sets fit neatly into the available SRAM space.
        A sample set will not be split over the end/beginning of
        the address-space.
        '''
        return int(self.comms_MCU.command_DAQ_MCU('a'))

    def get_size_of_SRAM_in_pages(self):
        '''
        Returns the number of 32-byte pages in the SRAM storage.
        '''
        return int(self.comms_MCU.command_DAQ_MCU('N'))

    def get_page_of_bytes(self, addr):
        '''
        Returns a 32-byte array, starting at byte-address addr.
        '''
        txt = self.comms_MCU.command_DAQ_MCU(f'M {addr}')
        return bytearray.fromhex(txt)

    def get_nsamples(self):
        '''
        Returns the number of samples after the trigger event.

        Note that this number should be treated as an unsigned integer.
        '''
        return self.get_reg(2)

    def get_formatted_sample(self, i):
        '''
        Returns the values of the recorded sample set i,
        where i is counted from the oldest recorded sample (i=0).

        The Pico2 reports these values as a string of space-separated integers.
        '''
        return [int(item) for item in self.comms_MCU.command_DAQ_MCU(f'P {i}').split()]

    #------------------------
    # Higher-level functions.
    #------------------------

    def get_recorded_data(self):
        '''
        Returns a list of lists containing the recorded values for each channel.

        This is a fairly slow way to get the full set of recorded samples
        because the Pico2 is doing all of the house-keeping and returning the
        sampled values as text strings.
        It may be faster to fetch the SRAM data in and then unpack the
        sample values on the PC.
        '''
        nchan = self.get_nchannels()
        _data = [[] for c in range(nchan)]
        #
        nsamples_after_trigger = self.get_nsamples()
        max_samples = self.get_max_nsamples()
        mode = self.get_trigger_mode()
        N = nsamples_after_trigger if mode==0 else max_samples
        for i in range(N):
            sample_values = self.get_formatted_sample(i)
            for j in range(nchan): _data[j].append(sample_values[j])
        return _data

    def fetch_SRAM_data(self, n_select=None, n_pretrigger=None):
        '''
        Returns a bytearray containing a selection of the SRAM data,
        along with enough metadata to interpret the bytes as samples.

        The selection is specified by:
        n_select     : the number of sample sets in the selection
        n_pretrigger : the number of sample sets before the trigger
        The default values of None indicate that we want as many as possible.

        Note that the bytearray will end up with the same data layout as the SRAM.
        '''
        DEBUG = True
        byte_addr_of_oldest_data = self.get_byte_address_of_oldest_data()
        total_bytes = self.get_size_of_SRAM_in_bytes()
        _ba = bytearray(total_bytes)
        total_pages = self.get_size_of_SRAM_in_pages()
        bytes_per_sample_set = self.get_byte_size_of_sample_set()
        nchan = self.get_nchannels()
        nsamples_after_trigger = self.get_nsamples()
        trigger_mode = self.get_trigger_mode()
        if trigger_mode == 0:
            # IMMEDIATE mode
            total_samples = nsamples_after_trigger
            nsamples_before_trigger = 0
        else:
            # Recording starts before trigger event,
            # at some indeterminant time.
            total_samples = self.get_max_nsamples()
            nsamples_before_trigger = total_samples - nsamples_after_trigger
        # The oldest sample set in SRAM has index 0.
        trigger_sample_index = nsamples_before_trigger
        if DEBUG:
            print(f'total_bytes={total_bytes}')
            print(f'total_pages={total_pages}')
            print(f'bytes_per_sample_set={bytes_per_sample_set}')
            print(f'byte_addr_of_oldest_data={byte_addr_of_oldest_data}')
            print(f'total_samples={total_samples}')
            print(f'nsamples_after_trigger={nsamples_after_trigger}')
            print(f'nsamples_before_trigger={nsamples_before_trigger}')
            print(f'trigger_sample_index={trigger_sample_index}')
        #
        # Work out the selection in terms of sample number,
        # and then again in page number (for the actual fetch).
        if n_select is None: n_select = total_samples
        n_select = min(n_select, total_samples)
        if n_pretrigger is None: n_pretrigger = nsamples_before_trigger
        n_pretrigger = min(n_pretrigger, nsamples_before_trigger)
        #
        # Depending on the number of channels, there can be a few sample sets
        # on each 32-byte page in SRAM.
        samples_per_page = 32 // bytes_per_sample_set
        first_sample_index = trigger_sample_index - n_pretrigger
        first_sample_byte_addr = byte_addr_of_oldest_data + bytes_per_sample_set * first_sample_index
        if first_sample_byte_addr > total_bytes: first_sample_byte_addr -= total_bytes
        first_page_index = first_sample_byte_addr // 32
        n_pages_to_get = n_select // samples_per_page
        # If the samples start part way through a page, we fetch an extra page to get the last few.
        if (first_sample_byte_addr % 32) != 0: n_pages_to_get += 1
        n_pages_to_get = min(n_pages_to_get, total_pages)
        if DEBUG:
            print(f'n_select={n_select}')
            print(f'n_pretrigger={n_pretrigger}')
            print(f'first_sample_index={first_sample_index}')
            print(f'samples_per_page={samples_per_page}')
            print(f'first_sample_byte_addr={first_sample_byte_addr}')
        print(f'About to fetch {n_pages_to_get} pages, starting at page {first_page_index}.')
        #
        # Fetch only the requested pages.
        for i in range(n_pages_to_get):
            addr = (i+first_page_index) * 32
            if addr >= total_bytes: addr -= total_bytes
            if i > 0 and (i % 100) == 0: print(f'page {i} byte-address {addr}')
            bpage = self.get_page_of_bytes(addr)
            for j in range(32): _ba[addr+j] = bpage[j]
        #
        # Other metadata to include with the bytearray.
        mode = self.get_trigger_mode()
        dt_us = self.get_sample_period_us()
        late_flag = self.did_not_keep_up_during_sampling()
        analog_gain = 1.0 # No choice for the BU79100G.
        ref_voltage = self.analog_millivolts()/1000
        return {'total_bytes':total_bytes,
                'total_pages':total_pages,
                'bytes_per_sample_set':bytes_per_sample_set,
                'byte_addr_of_oldest_data':byte_addr_of_oldest_data,
                'total_samples':total_samples,
                'nsamples_after_trigger': nsamples_after_trigger,
                'nsamples_before_trigger': nsamples_before_trigger,
                'nsamples_select': n_select,
                'nsamples_select_pretrigger': n_pretrigger,
                'first_sample_index': first_sample_index,
                'trigger_mode':self.trigger_modes_int_to_sym[mode],
                'nchan':nchan,
                'dt_us':dt_us,
                'late_flag':late_flag,
                'analog_gain':analog_gain,
                'ref_voltage':ref_voltage,
                'data':_ba}

    def unpack_to_samples(self, data):
        '''
        Given the dictionary containing the SRAM bytes and metadata,
        unpack those bytes into the channels of selected samples.

        The data is unwrapped such that the oldest sample is at index 0.
        Depending on the trigger mode, the index at the trigger event
        may be nonzero and is given by nsamples_select_pretrigger.
        '''
        nchan = data['nchan']
        bpss = data['bytes_per_sample_set']
        nbytes = data['total_bytes']
        byte_addr_of_oldest_data = data['byte_addr_of_oldest_data']
        nsamples_select = data['nsamples_select']
        first_sample_index = data['first_sample_index']
        # Note that the integers are sent from the Pico2 in big-endian format.
        s = struct.Struct(f'>{nchan}h')
        _samples = [[] for c in range(nchan)]
        for i in range(nsamples_select):
            # Unwrap the stored data so that the oldest data is at sample[0].
            addr = byte_addr_of_oldest_data + bpss * (i + first_sample_index)
            # Wrap to keep addr within the block of bytes, if necessary.
            # Note that sample sets should fit neatly within the byte array,
            # so we should only need to check the starting point for unpacking.
            while addr >= nbytes: addr -= nbytes
            items = s.unpack_from(data['data'], offset=addr)
            for j in range(nchan): _samples[j].append(items[j])
        return {'nchan':nchan,
                'nsamples_select':nsamples_select,
                'nsamples_select_pretrigger':data['nsamples_select_pretrigger'],
                'trigger_mode':data['trigger_mode'],
                'dt_us':data['dt_us'],
                'late_flag':data['late_flag'],
                'analog_gain':data['analog_gain'],
                'ref_voltage':data['ref_voltage'],
                'data':_samples}


if __name__ == '__main__':
    # A basic test to see if the eDAQS node is attached and awake.
    # Assuming that you have node '2', typical use on a Linux box:
    # $ python3 pic18f26q71_comms_3_mcu.py -i 2
    import time
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'E'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        node1 = PIC18F26Q71_COMMS_3_MCU(node_id, sp)
        print("Just some fiddling around to see that board is alive.")
        # We assume that a LED is attached to RA6
        # bits                                      decimal
        #    7    6    5    4    3    2    1    0    value
        #    X    X    X    X  RA6  RA5  RA4  RA2
        #    0    0    0    0    0    1    1    1  ==  7
        #    0    0    0    0    1    0    0    0  ==  8
        node1.utility_pins_write_ANSEL(7) # RA6 as digital; others analog
        node1.utility_pins_write_TRIS(7) # RA6 as output; others input
        node1.utility_pins_write_LAT(8) # set RA6 high to turn LED on
        print(node1.get_version())
        # If we have been reprogramming the DAQ_MCU while the COMMS_MCU is running,
        # we will likely have rubbish characters in its RX2 buffer.
        if not node1.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node1.reset_DAQ_MCU()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        daq_mcu = PICO2_DAQ_MCU_BU79100G(node1)
        print(daq_mcu.get_version())
        daq_mcu.set_regs_to_factory_values()
        print(daq_mcu.get_reg_values_as_text())
        print(f"Analog millivolts {daq_mcu.analog_millivolts()}")
        print("Report a few individual samples.")
        for i in range(5):
            print(daq_mcu.immediate_sample_set())
        time.sleep(1.0)
        node1.utility_pins_write_LAT(0) # turn LED off
    else:
        print("Did not find the serial port.")
    print("Done.")
