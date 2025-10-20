# usq_test_1.py
# Example for collecting 6 channels at 2kHz on one board, either node '8' or node '9'.
# Code Jeremy's channel arrangement directly for each node.
# Use immediate-mode trigger and record a full record.
#
# PJ 2024-11-13
#

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Example of recording six channels at 2kHz.")
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
    daq_mcu.set_AVR_sample_period_us(500)
    daq_mcu.set_AVR_analog_ref_voltage('4v096')
    daq_mcu.set_AVR_nsamples(4096*2)
    # daq_mcu.set_AVR_trigger_internal(0, 1000, 1)
    daq_mcu.set_AVR_trigger_immediate()
    if node_id == '8':
        daq_mcu.set_AVR_analog_channels([('AIN4','GND'),('AIN0','GND'),('AIN1','GND'),('AIN2','GND'),('AIN3','GND'),('AIN7','GND')])
    elif node_id == '9':
        daq_mcu.set_AVR_analog_channels([('AIN4','GND'),('AIN0','GND'),('AIN6','GND'),('AIN2','GND'),('AIN3','GND'),('AIN7','GND')])
    else:
        raise Error('Unknown node_id')
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
    my_data = daq_mcu.fetch_SRAM_data()
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch SRAM data")
    #
    # Now that we have our data, we can reset the AVR to release the Event# line.
    node1.reset_DAQ_MCU()
    node1.flush_rx2_buffer()
    #
    my_samples = daq_mcu.unpack_to_samples(my_data)
    print("Save the samples with metadata.")
    N = my_samples['total_samples']
    nchan = my_samples['nchan']
    dt_us = my_samples['dt_us']
    with open('samples.metadata', 'wt') as f:
        f.write(f'total_samples: {N}\n')
        f.write(f'nchan: {nchan}\n')
        f.write(f'nsamples_after_trigger: {my_samples["nsamples_after_trigger"]}\n')
        f.write(f'trigger_mode: {my_samples["trigger_mode"]}\n')
        f.write(f'dt_us: {dt_us}\n')
        f.write(f'late_flag: {my_samples["late_flag"]}\n')
        f.write(f'analog_gain: {my_samples["analog_gain"]}\n')
        f.write(f'ref_voltage: {my_samples["ref_voltage"]}\n')
    with open('samples.data', 'wt') as f:
        hdr = 't(ms) chan[0]'
        for j in range(1,nchan): hdr += f' chan[{j}]'
        hdr += '\n'
        f.write(hdr);
        for i in range(N):
            f.write('%g %d' % (i*dt_us/1000, my_samples['data'][0][i]))
            for j in range(1,nchan): f.write(' %d' % my_samples['data'][j][i])
            f.write('\n')

    #
    print("With the full record of samples, make a plot.")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(6,1)
    axs[0].set_title(f'Phil and Jeremys ramjet data board {node_id}')
    N = my_samples['total_samples']
    print(f"number of samples after trigger={my_samples['nsamples_after_trigger']}")
    for ch in range(6):
        axs[ch].plot(my_samples['data'][ch][0:N])
        axs[ch].set_ylabel('chan %d' % ch)
        axs[ch].set_ylim([-2500,2500])
    axs[5].set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    # Assuming node '8', typical use on a Linux box:
    # $ python3 usq_test_1.py -i 8
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '8'
    if args.identity: node_id = args.identity
    sp = openPort(port_name)
    if sp:
        main(sp, node_id)
    else:
        print("Did not find the serial port.")
    print("Done.")
