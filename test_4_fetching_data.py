# test_4_fetching_data.py

from rs485_edaq import *

def main(sp):
    node1 = EDAQSNode('1', sp)
    #
    print("Example of fetching all of the data after a recording.")
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
    #
    print("About to fetch data...")
    start = time.time()
    my_data = node1.fetch_SRAM_data()
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch SRAM data")
    my_samples = node1.unpack_to_samples(my_data)
    #
    print("With the post-trigger samples, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1) = plt.subplots(2,1)
    ax0.set_title('AVR64EA28 eDAQS sampled data')
    N = my_samples['nsamples_after_trigger'] # IMMEDIATE_MODE recording
    ax0.plot(my_samples['data'][0][0:N]); ax0.set_ylabel('chan 0')
    ax1.plot(my_samples['data'][1][0:N]); ax1.set_ylabel('chan 1')
    ax1.set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        main(sp)
    else:
        print("Did not find the serial port.")
    print("Done.")
