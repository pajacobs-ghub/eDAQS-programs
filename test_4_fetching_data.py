# test_4_fetching_data.py

from rs485_edaq import *
import struct

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Fetch all of the data after a recording.")
        print(node1.get_PIC_version())
        if not node1.test_AVR_is_ready():
            print("Reset AVR")
            node1.reset_AVR()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        print(node1.get_AVR_version())
        #
        print("Make a recording.")
        node1.set_AVR_sample_period_us(1000)
        node1.set_AVR_nsamples(2000)
        node1.set_AVR_trigger_immediate()
        node1.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
        node1.clear_AVR_PGA()
        # node1.print_AVR_reg_values()
        print("AVR ready: ", node1.test_AVR_is_ready())
        print("event has passed: ", node1.test_event_has_passed())
        node1.start_AVR_sampling()
        ready = node1.test_AVR_is_ready()
        while not ready:
            print('Waiting...')
            time.sleep(0.1)
            ready = node1.test_AVR_is_ready()
        print("event has passed: ", node1.test_event_has_passed())
        nchan = node1.get_AVR_nchannels()
        nsamples = node1.get_AVR_nsamples()
        mode = node1.get_AVR_trigger_mode()
        print(f"nchan={nchan}, nsamples={nsamples}, trigger_mode={mode}")
        #
        print("About to fetch data...")
        start = time.time()
        my_data = node1.fetch_SRAM_data()
        elapsed = time.time() - start
        print(f"{elapsed:.2f} seconds to fetch SRAM data")
        print(f"nbytes={my_data['nbytes']}")
        print(f"npages={my_data['npages']}")
        bpss = my_data['bytes_per_sample_set']
        print(f"bytes_per_sample_set={bpss}")
        #
        print("Extract sample values.")
        # Note that the integers are stored in the SRAM chip in big-endian format.
        s = struct.Struct(f'>{nchan}h')
        my_samples = [[] for c in range(nchan)]
        for i in range(nsamples):
            addr = bpss * i
            items = s.unpack_from(my_data['data'], offset=addr)
            for j in range(nchan): my_samples[j].append(items[j])
        #
        print("With those samples, make a plot.")
        import matplotlib.pyplot as plt
        fig, (ax0,ax1) = plt.subplots(2,1)
        ax0.set_title('AVR64EA28 eDAQS sampled data')
        ax0.plot(my_samples[0]); ax0.set_ylabel('chan 0')
        ax1.plot(my_samples[1]); ax1.set_ylabel('chan 1')
        ax1.set_xlabel('sample number')
        plt.show()
    else:
        print("Did not find the serial port.")
    print("Done.")
