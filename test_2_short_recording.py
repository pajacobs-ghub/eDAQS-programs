# test_2_short_recording.py

from rs485_edaq import *

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Example of a short recording.")
        print(node1.get_PIC_version())
        if not node1.test_AVR_is_ready():
            print("Reset AVR")
            node1.reset_AVR()
            time.sleep(2.0)
        node1.flush_rx2_buffer()
        print(node1.get_AVR_version())
        #
        node1.clear_AVR_PGA()
        node1.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
        node1.set_AVR_sample_period_us(1000)
        node1.set_AVR_nsamples(20)
        node1.set_AVR_trigger_immediate()
        node1.print_AVR_reg_values()
        print("AVR ready: ", node1.test_AVR_is_ready())
        print("event has passed: ", node1.test_event_has_passed())
        node1.start_AVR_sampling()
        ready = node1.test_AVR_is_ready()
        while not ready:
            print('Waiting...')
            time.sleep(0.01)
            ready = node1.test_AVR_is_ready()
        # After sampling is done.
        print("event has passed: ", node1.test_event_has_passed())
        nchan = node1.get_AVR_nchannels()
        nsamples = node1.get_AVR_nsamples()
        mode = node1.get_AVR_trigger_mode()
        print(f"nchan={nchan}, nsamples={nsamples}, trigger_mode={mode}")
        bytes_per_sample = node1.get_AVR_byte_size_of_sample_set()
        max_samples = node1.get_AVR_max_nsamples()
        size_of_SRAM = node1.get_AVR_size_of_SRAM_in_bytes()
        print(f"bytes_per_sample={bytes_per_sample}, size_of_SRAM={size_of_SRAM}")
        print(f"max_samples={max_samples}")
        for i in range(nsamples):
            items = node1.get_AVR_formatted_sample(i)
            print(items)
    else:
        print("Did not find the serial port.")
    print("Done.")
