# test_8_20kHz_record.py
# Example for collecting two channels of data for the repetitive shock tube.
# PJ 2024-10-08
#    2025-07-20 : Selectively fetch the recorded data.
#
# The physical input for my test was a signal generator running continuously.
# 2024-10-08
#   AIN28 - 0-4V sine wave at 10Hz from Rigol signal gen.
#   AIN29 - 0-2V square wave at 10Hz and synchronised with the sine wave.
# 2025-07-20: feed via voltage divider (signal gen was 0-4V)
#   AIN28 - 0-2V sine wave at 10Hz
#   AIN29 - 0-2V sine wave at 10Hz
#
# It is expected that, with a cyclic and continuous input,
# the trigger will happen immediately.

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Example of recording two channels at 20kHz.")
    print(node1.get_PIC_version())
    if not node1.test_DAQ_MCU_is_ready():
        print("Reset DAQ_MCU")
        node1.reset_DAQ_MCU()
        time.sleep(2.0)
    node1.flush_rx2_buffer()
    daq_mcu = AVR64EA28_DAQ_MCU(node1)
    print(daq_mcu.get_AVR_version())
    #
    print("Make a recording.")
    daq_mcu.set_AVR_sample_period_us(50)
    daq_mcu.set_AVR_analog_ref_voltage('4v096')
    daq_mcu.set_AVR_nsamples(16384)
    daq_mcu.set_AVR_trigger_internal(0, 500, 1)
    daq_mcu.set_AVR_single_sided_conversion()
    daq_mcu.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
    daq_mcu.clear_AVR_PGA()
    daq_mcu.set_AVR_burst(0)
    print("DAQ_MCU ready: ", node1.test_DAQ_MCU_is_ready())
    #
    # Make sure that PIC has not been asked to hold EVENT# low.
    node1.release_event_line()
    node1.disable_external_trigger()
    print("Before enabling trigger, result of Q command:", node1.command_PIC('Q'))
    #
    daq_mcu.start_AVR_sampling()
    while not node1.test_event_has_passed():
        print("Waiting for trigger...")
        time.sleep(1.0)
    print("After trigger, result of Q command:", node1.command_PIC('Q'))
    # Even though event has passed, the AVR may be still sampling.
    ready = node1.test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting for DAQ_MCU...')
        time.sleep(0.1)
        ready = node1.test_DAQ_MCU_is_ready()
    #
    print(f"AVR late sampling={daq_mcu.AVR_did_not_keep_up_during_sampling()}")
    print("About to fetch data...")
    start = time.time()
    # my_data = daq_mcu.fetch_SRAM_data()
    my_data = daq_mcu.fetch_SRAM_data(n_select=2000, n_pretrigger=200)
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch SRAM data")
    #
    # Now that we have our data, we can reset the AVR to release the Event# line.
    node1.reset_DAQ_MCU()
    node1.flush_rx2_buffer()
    #
    my_samples = daq_mcu.unpack_to_samples(my_data)
    print("Save the samples with metadata.")
    N = my_samples['nsamples_select']
    nchan = my_samples['nchan']
    dt_us = my_samples['dt_us']
    with open('samples.metadata', 'wt') as f:
        f.write(f'nsamples_select: {N}\n')
        f.write(f'nchan: {nchan}\n')
        f.write(f'nsamples_select_pretrigger: {my_samples["nsamples_select_pretrigger"]}\n')
        f.write(f'trigger_mode: {my_samples["trigger_mode"]}\n')
        f.write(f'dt_us: {dt_us}\n')
        f.write(f'late_flag: {my_samples["late_flag"]}\n')
        f.write(f'analog_gain: {my_samples["analog_gain"]}\n')
        f.write(f'ref_voltage: {my_samples["ref_voltage"]}\n')
    with open('samples.data', 'wt') as f:
        hdr = f't(ms) chan[0]'
        for j in range(1,nchan): hdr += f' chan[{j}]'
        hdr += '\n'
        f.write(hdr);
        for i in range(N):
            f.write('%g %d' % (i*dt_us/1000, my_samples['data'][0][i]))
            for j in range(1,nchan): f.write(' %d' % my_samples['data'][j][i])
            f.write('\n')

    #
    print("With the selected samples, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1) = plt.subplots(2,1)
    ax0.set_title('AVR64EA28 eDAQS sampled data')
    N = my_samples['nsamples_select']
    print(f"nsamples_select_pretrigger={my_samples['nsamples_select_pretrigger']}")
    ax0.plot(my_samples['data'][0][0:N]); ax0.set_ylabel('chan 0')
    ax1.plot(my_samples['data'][1][0:N]); ax1.set_ylabel('chan 1')
    ax1.set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    # Assuming node '1', typical use on a Linux box:
    # $ python3 test_8_20kHz_record.py -i 1
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
