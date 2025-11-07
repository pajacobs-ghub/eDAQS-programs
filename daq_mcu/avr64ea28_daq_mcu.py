# avr64ea28_daq_mcu.py
#
# Peter J.
# 2025-10-20: Extracted from the v1 code.
#
import sys
sys.path.append("..")
from comms_mcu import rs485
from comms_mcu.pic18f16q41_comms_1_mcu import PIC18F16Q41_COMMS_1_MCU
import struct

class AVR64EA28_DAQ_MCU(object):
    """
    DAC_MCU service functions for an AVR64EA28 microcontroller on the avr-edaq-1 board.
    """

    __slots__ = ['comms_MCU', 'n_reg', 'reg_labels', 'reg_labels_to_int',
                 'pins', 'pins_int_to_sym', 'channels',
                 'ref_voltages', 'ref_voltages_int_to_value',
                 'pga_gains', 'pga_gains_int_to_value',
                 'sample_accumulation_number',
                 'trigger_modes', 'trigger_modes_int_to_sym',
                 'trigger_slopes', 'trigger_slopes_int_to_sym',
                 'us_per_tick']

    def __init__(self, comms_MCU):
        '''
        We do all of the interaction with the DAQ_MCU through the COMMS_MCU.
        '''
        self.comms_MCU = comms_MCU
        #
        # The following data should match the firmware programmed into the AVR.
        # A dictionary is used so that it is easy to cross-check the labels.
        self.n_reg = 36
        self.reg_labels = {
            0:'PER_TICKS', 1:'NCHANNELS', 2:'NSAMPLES',
            3:'TRIG_MODE', 4:'TRIG_CHAN', 5:'TRIG_LEVEL', 6:'TRIG_SLOPE',
            7:'PGA_FLAG', 8:'PGA_GAIN', 9:'V_REF',
            10:'CH0+', 11:'CH0-', 12:'CH1+', 13:'CH1-', 14:'CH2+', 15:'CH2-',
            16:'CH3+', 17:'CH3-', 18:'CH4+', 19:'CH4-', 20:'CH5+', 21:'CH5-',
            22:'CH6+', 23:'CH6-', 24:'CH7+', 25:'CH7-', 26:'CH8+', 27:'CH8-',
            28:'CH9+', 29:'CH9-', 30:'CH10+', 31:'CH10-', 32:'CH11+', 33:'CH11-',
            34:'NBURST', 35: 'DIFF_CONV'
        }
        assert self.n_reg == len(self.reg_labels), "Oops, check reg_labels."
        self.reg_labels_to_int = {
            'PER_TICKS':0, 'NCHANNELS':1, 'NSAMPLES':2,
            'TRIG_MODE':3, 'TRIG_CHAN':4, 'TRIG_LEVEL':5, 'TRIG_SLOPE':6,
            'PGA_FLAG':7, 'PGA_GAIN':8, 'V_REF':9,
            'CH0+':10, 'CH0-':11, 'CH1+':12, 'CH1-':13, 'CH2+':14, 'CH2-':15,
            'CH3+':16, 'CH3-':17, 'CH4+':18, 'CH4-':19, 'CH5+':20, 'CH5-':21,
            'CH6+':22, 'CH6-':23, 'CH7+':24, 'CH7-':25, 'CH8+':26, 'CH8-':27,
            'CH9+':28, 'CH9-':29, 'CH10+':30, 'CH10-':31, 'CH11+':32, 'CH11-':33,
            'NBURST':34, 'DIFF_CONV':35
        }
        assert self.n_reg == len(self.reg_labels_to_int), "Oops, check reg_labels_to_int."
        # Give names to the analog-in pins to make it easy to specify analog inputs.
        self.pins = {
            'AIN28':28, 'PC0':28, 28:28, 'AIN29':29, 'PC1':29, 29:29,
            'AIN30':30, 'PC2':30, 30:30, 'AIN31':31, 'PC3':30, 31:31,
            'AIN0':0, 'PD0':0, 0:0, 'AIN1':1, 'PD1':1, 1:1,
            'AIN2':2, 'PD2':2, 2:2, 'AIN3':3, 'PD3':3, 3:3,
            'AIN4':4, 'PD4':4, 4:4, 'AIN5':5, 'PD5':5, 5:5,
            'AIN6':6, 'PD6':6, 6:6, 'AIN7':7, 'PD2':7, 7:7,
            'GND':48
        }
        self.pins_int_to_sym = {
            28:'AIN28', 29:'AIN29',
            30:'AIN30', 31:'AIN31',
            0:'AIN0', 1:'AIN1',
            2:'AIN2', 3:'AIN3',
            4:'AIN4', 5:'AIN5',
            6:'AIN6', 7:'AIN7',
            48:'GND'
        }
        self.channels = [] # to be filled in via function calls, later
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
        self.trigger_modes = {
            'IMMEDIATE':0, 0:0,
            'INTERNAL':1, 1:1,
            'EXTERNAL':2, 2:2
        }
        self.trigger_modes_int_to_sym = {
            0:'IMMEDIATE',
            1:'INTERNAL',
            2:'EXTERNAL'
        }
        self.trigger_slopes = {
            'NEG':0, 'BELOW':0, 0:0,
            'POS':1, 'ABOVE':1, 1:1
        }
        self.trigger_slopes_int_to_sym = {
            0:'NEG',
            1:'POS'
        }
        self.us_per_tick = 0.8 # Hardware timer set at this value.
        return

    def get_version(self):
        return self.comms_MCU.command_DAQ_MCU('v')

    def get_n_reg_actual(self):
        '''
        Get the actual number of virtual registers in the AVR MCU.
        This may be differ with firmware version.
        '''
        txt = self.comms_MCU.command_DAQ_MCU('n')
        return int(txt)

    def get_reg(self, i):
        '''
        Returns the value of the i-th pseudo-register.
        '''
        n_reg_actual = self.get_n_reg_actual()
        if i >= n_reg_actual:
            raise RuntimeError(f'Requested register {i} but n_reg_actual is {n_reg_actual}.')
        txt = self.comms_MCU.command_DAQ_MCU(f'r {i}')
        return int(txt)

    def set_reg(self, i, val):
        '''
        Sets the value of the i-th pseudo-register and
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
        Set a number of AVR registers from values in a dictionary.

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
        Sets the AVR ticks register to (approximately) achieve
        the sample period in microseconds.
        '''
        ticks = int(dt_us / self.us_per_tick)
        # [TODO] should put some checks on this.
        self.set_reg(0, ticks)
        return

    def get_sample_period_us(self):
        '''
        Returns sample period in microseconds.
        '''
        return self.get_reg(0) * self.us_per_tick

    def set_analog_channels(self, chan_list):
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
        self.set_reg(1, nchan)
        for i in range(nchan):
            self.set_reg(10+i*2, self.channels[i][0])
            self.set_reg(11+i*2, self.channels[i][1])
        return

    def set_PGA(self, gain='8X'):
        '''
        '''
        self.set_reg(7, 1) # via PGA
        self.set_reg(8, self.pga_gains[gain])
        return

    def clear_PGA(self):
        '''
        '''
        self.set_reg(7, 0) # direct
        self.set_reg(8, 0) # 1X
        return

    def get_analog_gain(self):
        '''
        '''
        pga_flag = self.get_reg(7)
        if pga_flag == 0:
            return 1
        elif pga_flag == 1:
            return self.pga_gains_int_to_value[self.get_reg(8)]

    def set_analog_ref_voltage(self, vStr):
        '''
        Select the reference voltage from a symbolic name.
        'VDD', '1v024', '2v048', '4v096', or '2v500'
        '''
        refVsel = self.ref_voltages['4v096']
        try:
            refVsel = self.ref_voltages[vStr]
        except:
            refVsel = self.ref_voltages['4v096']
        self.set_reg(9, refVsel)
        return

    def get_burst_samples(self):
        return 2**self.get_AVR_reg(34)

    def set_burst(self, n):
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
        self.set_reg(34, log2n)
        return

    def get_analog_ref_voltage(self):
        '''
        '''
        return self.ref_voltages_int_to_value[self.get_reg(9)]

    def set_differential_conversion(self):
        '''
        '''
        self.set_reg(35, 1)
        return

    def set_single_sided_conversion(self):
        '''
        '''
        self.set_reg(35, 0)
        return

    def immediate_sample_set(self):
        '''
        '''
        txt = self.comms_MCU.command_DAQ_MCU('I')
        return txt

    def set_trigger_immediate(self):
        '''
        Set the trigger mode to IMMEDIATE.

        Recording will start immediately that the MCU is told to start sampling
        and will stop after nsamples have been recorded.
        '''
        self.set_reg(3, self.trigger_modes['IMMEDIATE'])
        return

    def set_trigger_internal(self, chan, level, slope):
        '''
        Set the trigger mode to INTERNAL.

        Recording will start immediately that the MCU is told to start sampling
        and will continue indefinitely, until the specified channel crosses
        the specified level.
        nsamples with then be recorded and the sampling stops after than.
        '''
        # [TODO] some checking for reasonable input.
        self.set_reg(3, self.trigger_modes['INTERNAL'])
        self.set_reg(4, chan)
        self.set_reg(5, level)
        self.set_reg(6, self.trigger_slopes[slope])
        return

    def set_trigger_external(self):
        '''
        Set the trigger mode to EXTERNAL.

        Recording will start immediately that the MCU is told to start sampling
        and will continue indefinitely, until the EVENT# pin goes low.
        nsamples with then be recorded and the sampling stops after than.
        '''
        self.set_reg(3, self.trigger_modes['EXTERNAL'])
        return

    def set_nsamples(self, n):
        '''
        Set the number of samples to be recorded after trigger event.
        '''
        # [TODO] some checking for reasonable input.
        if n < 0: n = 100 # Somewhat arbitrary.
        # The AVR firmware is reports value as a 16-bit signed integer,
        # so let's avoid setting values too large.
        if n > 32767: n = 32767
        self.set_reg(2, n)
        return

    def start_sampling(self):
        '''
        Start the AVR sampling.

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
        indicate that the AVR did not kep up during sampling.
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

        This value is dependent on the total amount of SRAM installed
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

    def get_trigger_mode(self):
        '''
        Returns the integer value representing the trigger mode.
        '''
        return self.get_reg(3)

    def get_formatted_sample(self, i):
        '''
        Returns the values of the recorded sample set i,
        where i is counted from the oldest recorded sample (i=0).

        The AVR reports these values as a string of space-separated integers.
        '''
        return [int(item) for item in self.comms_MCU.command_DAQ_MCU(f'P {i}').split()]

    #------------------------
    # Higher-level functions.
    #------------------------

    def get_recorded_data(self):
        '''
        Returns a list of lists containing the recorded values for each channel.

        This is a fairly slow way to get the full set of recorded samples
        because the AVR is doing all of the house-keeping and returning the
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
        analog_gain = self.get_analog_gain()
        ref_voltage = self.get_analog_ref_voltage()
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
        # Note that the integers are stored in the SRAM chip in big-endian format.
        s = struct.Struct(f'>{nchan}h')
        _samples = [[] for c in range(nchan)]
        for i in range(nsamples_select):
            # Unwrap the stored data so that the oldest data is at sample[0].
            addr = byte_addr_of_oldest_data + bpss * (i + first_sample_index)
            if addr >= nbytes: addr -= nbytes
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
        node1 = PIC18F16Q41_COMMS_1_MCU(node_id, sp)
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
        daq_mcu = AVR64EA28_DAQ_MCU(node1)
        print(daq_mcu.get_version())
        print("size of SRAM (bytes)=", daq_mcu.get_size_of_SRAM_in_bytes())
        print(daq_mcu.get_reg(0))
        print(daq_mcu.set_reg(0, 250))
        print(daq_mcu.get_reg(0))
        daq_mcu.set_regs_to_factory_values()
        daq_mcu.set_regs_from_dict({1:6, 2:100})
        print(daq_mcu.get_reg_values_as_text())
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
