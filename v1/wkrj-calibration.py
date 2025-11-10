# WKRJ-calibration.py
# For collecting a brief sample for calibration, 6 channels at 8kHz on each of two boards, nodes 'A' and '8' for the Weston K Ramjet at USQ
# JM 2025-07-23 added single-sided conversion and analog reference voltage
# JM 2025-11-10 added to the repo "as is" from the Weston K Ramjet project


from rs485_edaq import *
import datetime


NSELECT = 100  # number of samples to fetch after the trigger
NPRETRIGGER = 10  # number of samples to fetch before the trigger
VREF = '2v500'  # analog reference voltage


# Get the current date and time
now = datetime.datetime.now()
timestamp = now.strftime("%Y%m%d_%H%M")

def main(sp, node_ids):
    nboards = len(node_ids)
    nodes = [EDAQSNode(node_ids[j], sp) for j in range(nboards)]
    #
    print("WKRJ recording six channels at 8kHz.")
    for node in nodes:
        print(node.get_PIC_version())
        if not node.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node.reset_DAQ_MCU()
            time.sleep(2.0)
        node.flush_rx2_buffer()
    daq_mcus = [AVR64EA28_DAQ_MCU(node) for node in nodes]
    for daq_mcu in daq_mcus:
        print(daq_mcu.get_AVR_version())
    #
    print("Make a recording.")
    daq_mcus[0].set_AVR_analog_ref_voltage('VDD')
    daq_mcus[1].set_AVR_analog_ref_voltage(VREF)
    for daq_mcu in daq_mcus:
        daq_mcu.set_AVR_sample_period_us(125)
        #daq_mcu.set_AVR_analog_ref_voltage(VREF)
        daq_mcu.set_AVR_single_sided_conversion()
        daq_mcu.set_AVR_nsamples(4096)
        daq_mcu.set_AVR_trigger_external()

    daq_mcus[0].set_AVR_analog_channels([('AIN0','GND'),('AIN1','GND'),('AIN2','GND'),
                                         ('AIN3','GND'), ('AIN4','GND'), ('AIN5','GND')])
    daq_mcus[1].set_AVR_analog_channels([('AIN0','GND'),('AIN1','GND'),('AIN2','GND'),
                                         ('AIN3','GND'),('AIN4','GND'),('AIN5','GND')])
    for daq_mcu in daq_mcus:
        daq_mcu.clear_AVR_PGA()
        daq_mcu.set_AVR_burst(0)
    for node in nodes:
        print("DAQ_MCU ready: ".format(node.test_DAQ_MCU_is_ready()))
        #
        # Make sure that PIC has not been asked to hold EVENT# low.
        node.release_event_line()
        node.disable_external_trigger()
        print("Before enabling trigger, result of Q command:", node.command_PIC('Q'))
    #
    nodes[0].disable_external_trigger() # depends on node 'A' for event signal
    nodes[1].enable_external_trigger(100, 'pos') # on node 'A'

    for daq_mcu in daq_mcus:
        daq_mcu.start_AVR_sampling()
    while not nodes[1].test_event_has_passed():
        print("Waiting for trigger...")
        time.sleep(1.0)
    for node in nodes:
        print("After trigger, result of Q command:", node.command_PIC('Q'))
    # Even though event has passed, the AVRs may be still sampling.
    ready = nodes[1].test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting for DAQ_MCU on node A...')
        time.sleep(0.1)
        ready = nodes[1].test_DAQ_MCU_is_ready()
    ready = nodes[0].test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting for DAQ_MCU on node 8...')
        time.sleep(0.1)
        ready = nodes[1].test_DAQ_MCU_is_ready()
    #
    for daq_mcu in daq_mcus:
        print(f"AVR late sampling={daq_mcu.AVR_did_not_keep_up_during_sampling()}")
    print("About to fetch data...")
    start = time.time()
    my_data_sets = [daq_mcu.fetch_SRAM_data(n_select=NSELECT, n_pretrigger=NPRETRIGGER) for daq_mcu in daq_mcus]
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch SRAM data")
    #
    # Now that we have our data, we can reset the AVR to release the Event# line.
    for node in nodes:
        node.reset_DAQ_MCU()
        node.flush_rx2_buffer()
    #
    my_sample_sets = [daq_mcus[j].unpack_to_samples(my_data_sets[j]) for j in range(nboards)]
    print("Save the samples with metadata.")
    for j in range(nboards):
        my_samples = my_sample_sets[j]
        N = my_samples['nsamples_select']
        nchan = my_samples['nchan']
        dt_us = my_samples['dt_us']
        with open(f'calibration-{j}.metadata', 'wt') as f:
            f.write(f'nsamples_select: {N}\n')
            f.write(f'nchan: {nchan}\n')
            f.write(f'nsamples_select_pretrigger: {my_samples["nsamples_select_pretrigger"]}\n')
            f.write(f'trigger_mode: {my_samples["trigger_mode"]}\n')
            f.write(f'dt_us: {dt_us}\n')
            f.write(f'late_flag: {my_samples["late_flag"]}\n')
            f.write(f'analog_gain: {my_samples["analog_gain"]}\n')
            f.write(f'ref_voltage: {my_samples["ref_voltage"]}\n')
        with open(f'calibration-{j}.data', 'wt') as f:
            hdr = f't(ms) chan[0]'
            for j in range(1,nchan): hdr += f' chan[{j}]'
            hdr += '\n'
            f.write(hdr);
            for i in range(N):
                f.write('%g %d' % (i*dt_us/1000, my_samples['data'][0][i]))
                for j in range(1,nchan): f.write(' %d' % my_samples['data'][j][i])
                f.write('\n')

    #

    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 usq_test_2.py
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = 'COM3'
    if args.port: port_name = args.port
    node_ids = ['8', 'A']
    sp = openPort(port_name)
    if sp:
        main(sp, node_ids)
        sp.close()
    else:
        print("Did not find the serial port.")
    
    print("Done.")
