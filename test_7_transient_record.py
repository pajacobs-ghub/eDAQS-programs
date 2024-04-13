# test_7_transient_record.py

from rs485_edaq import *

def main(sp):
    node1 = EDAQSNode('1', sp)
    #
    print("Example of a transient-capture recording.")
    print(node1.get_PIC_version())
    if not node1.test_AVR_is_ready():
        print("Reset AVR")
        node1.reset_AVR()
        time.sleep(2.0)
    node1.flush_rx2_buffer()
    print(node1.get_AVR_version())
    #
    print("Make a recording.")
    node1.set_AVR_sample_period_us(100)
    node1.set_AVR_nsamples(20000)
    node1.set_AVR_trigger_external()
    node1.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
    node1.clear_AVR_PGA()
    # node1.print_AVR_reg_values()
    print("AVR ready: ", node1.test_AVR_is_ready())
    #
    # Make sure that PIC has not been asked to hold EVENT# low.
    node1.release_event_line()
    node1.disable_external_trigger()
    print("Before enabling trigger, result of Q command:", node1.command_PIC('Q'))
    #
    node1.enable_external_trigger(128, 'pos')
    node1.start_AVR_sampling()
    while not node1.test_event_has_passed():
        print("Waiting for trigger...")
        time.sleep(1.0)
    print("After trigger, result of Q command:", node1.command_PIC('Q'))
    node1.disable_external_trigger()
    # Even though event has passed, the AVR may be still sampling.
    ready = node1.test_AVR_is_ready()
    while not ready:
        print('Waiting for AVR...')
        time.sleep(0.1)
        ready = node1.test_AVR_is_ready()
    #
    print(f"AVR late sampling={node1.AVR_did_not_keep_up_during_sampling()}")
    print("About to fetch data...")
    start = time.time()
    my_data = node1.fetch_SRAM_data()
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch SRAM data")
    my_samples = node1.unpack_to_samples(my_data)
    #
    print("With the full record of samples, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1) = plt.subplots(2,1)
    ax0.set_title('AVR64EA28 eDAQS sampled data')
    N = my_samples['total_samples']
    print(f"number of samples after trigger={my_samples['nsamples_after_trigger']}")
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
