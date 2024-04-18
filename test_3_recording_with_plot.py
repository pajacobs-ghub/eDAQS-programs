# test_3_recording_with_plot.py

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Example of a recording with plot of collected data.")
    print(node1.get_PIC_version())
    if not node1.test_DAQ_MCU_is_ready():
        print("Reset DAQ_MCU")
        node1.reset_DAQ_MCU()
        time.sleep(2.0)
    node1.flush_rx2_buffer()
    daq_mcu = AVR64EA28_DAQ_MCU(node1)
    print(daq_mcu.get_AVR_version())
    #
    print("Make a longer recording.")
    daq_mcu.set_AVR_sample_period_us(1000)
    daq_mcu.set_AVR_nsamples(2000)
    daq_mcu.set_AVR_trigger_immediate()
    daq_mcu.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
    daq_mcu.clear_AVR_PGA()
    # daq_mcu.print_AVR_reg_values()
    print("AVR ready: ", node1.test_DAQ_MCU_is_ready())
    print("event has passed: ", node1.test_event_has_passed())
    daq_mcu.start_AVR_sampling()
    ready = node1.test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting...')
        time.sleep(0.1)
        ready = node1.test_DAQ_MCU_is_ready()
    print("event has passed: ", node1.test_event_has_passed())
    nchan = daq_mcu.get_AVR_nchannels()
    nsamples = daq_mcu.get_AVR_nsamples()
    mode = daq_mcu.get_AVR_trigger_mode()
    print(f"nchan={nchan}, nsamples={nsamples}, trigger_mode={mode}")
    print("About to fetch data...")
    start = time.time()
    my_data = daq_mcu.get_recorded_data()
    # print("my_data=", my_data)
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch {nsamples} sample sets")
    #
    print("With that recorded data, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1) = plt.subplots(2,1)
    ax0.set_title('AVR64EA28 eDAQS sampled data')
    ax0.plot(my_data[0]); ax0.set_ylabel('chan 0')
    ax1.plot(my_data[1]); ax1.set_ylabel('chan 1')
    ax1.set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_3_recording_with_plot.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '1'
    if args.identity: node_id = args.identity
    sp = openPort(port_name)
    if sp:
        main(sp, node_id)
    else:
        print("Did not find the serial port.")
    print("Done.")
