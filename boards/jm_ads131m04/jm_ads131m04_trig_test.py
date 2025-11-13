# jm_ads131m04_trig_test.py
# This script is specific to Jeremy's "SUPER-ADC ADS131M04" board, either Revision B or C.
# Arm eDAQS to wait for an external trigger signal, then take a single sample and report the values.
#
# JM 2025-11-09    First pass, adapted from diff_spec_monitor.py and test_6_external_trigger.py.
import sys
sys.path.append("../..")
import time
import os
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
from daq_mcu.pico2_ads131m04 import PICO2_ADS131M04_DAQ
from jm_ads131m04_plot import plot_channels
import struct

NSAMPLES = 256  # number of samples to fetch after the trigger
NPRETRIGGER = 256  # number of samples to fetch before the trigger

def main(sp, node_id, fileName):
    print("\n =====================================")
    print(" SUPER-ADC ADS131M04 TRIGGER TEST.")
    print(" version 2025-11-10 JM")
    print(" =====================================\n")
    node = PIC18F16Q41_JM_ADS131M04_COMMS(node_id, sp)
    daq = PICO2_ADS131M04_DAQ(node)

    # Get versions, and reset DAQ_MCU
    print(node.get_version())
    node.reset_DAQ_MCU()
    time.sleep(1.6)
    print(daq.get_version())


    # Configure ADS131M04
    daq.set_clk(8192)  # Set clock to 8192 kHz
    daq.release_pico2_event() # Make sure Pico2-EVENT# line is released if not already
    daq.set_osr(1024) # Default OSR
    daq.set_trigger_mode(2)  # External trigger
    #daq.set_trigger_mode(0)  # immediate trigger for testing
    daq.set_num_samples(NSAMPLES)  # samples per channel
    print("DAQ_MCU ready: ", node.test_DAQ_MCU_is_ready())
    time.sleep(0.1)
    print("Maximum number of samples storable in SRAM:", node.command_DAQ_MCU('m'))

    # Make sure that PIC has not been asked to hold SYS-EVENT# low.
    node.release_event_line()
    node.disable_external_trigger()
    print("Before enabling trigger, result of Q command:", node.command_COMMS_MCU('Q'))
    node.enable_external_trigger(200, 'pos')
    node.set_LED(1) # Turn on LED to indicate waiting for trigger
    
    # tell the DAQ to start its sampling process
    daq.sample()  # Start sampling process

    # Wait for trigger event
    start_time = time.time()
    while not node.test_event_has_passed():
        elapsed = time.time() - start_time
        print(f"\r  Waiting for trigger... {elapsed:.1f}s", end='', flush=True)
        time.sleep(0.2)
    elapsed = time.time() - start_time
    print("\nAfter trigger, result of Q command:", node.command_COMMS_MCU('Q'))

    # Even though event has passed, the DAQ_MCU may be still sampling.
    ready = node.test_DAQ_MCU_is_ready()
    daq_start_time = time.time()
    while not ready:
        daq_elapsed = time.time() - daq_start_time
        print(f'\r  Waiting for DAQ_MCU... {daq_elapsed:.1f}s', end='', flush=True)
        time.sleep(0.1)
        ready = node.test_DAQ_MCU_is_ready()
    print("\nAfter waiting for DAQ, result of Q command:", node.command_COMMS_MCU('Q'))

    node.disable_external_trigger()
    daq.error_flags()
    node.set_LED(0)

    # After sampling completes
    result = daq.fetch_SRAM_data(n_pretrigger=NPRETRIGGER)

    # Access the data
    data_bytes = result['data']
    n_pre = result['nsamples_before_trigger']
    n_post = result['nsamples_after_trigger']
    total_samples = n_pre + n_post
    nchan = result['nchan']
    dt_us = result['dt_us']

    print(f"\nSaving data to {fileName}...")
    
    # Save metadata file
    metadata_file = fileName.replace('.dat', '.metadata')
    with open(metadata_file, 'wt') as f:
        f.write(f'nsamples_total: {total_samples}\n')
        f.write(f'nchan: {nchan}\n')
        f.write(f'nsamples_before_trigger: {n_pre}\n')
        f.write(f'nsamples_after_trigger: {n_post}\n')
        f.write(f'trigger_index: {result["first_sample_index"]}\n')
        f.write(f'trigger_mode: {result["trigger_mode"]}\n')
        f.write(f'dt_us: {dt_us}\n')
        f.write(f'index_of_oldest_data: {result["index_of_oldest_data"]}\n')
    
    # Save data file with samples
    with open(fileName, 'wt') as f:
        # Write header
        hdr = 't(us) chan[0] chan[1] chan[2] chan[3]\n'
        f.write(hdr)
        
        # Write data
        for i in range(total_samples):
            offset = i * 16
            ch0, ch1, ch2, ch3 = struct.unpack('<4i', data_bytes[offset:offset+16])
            f.write(f'{i*dt_us:.6f} {ch0} {ch1} {ch2} {ch3}\n')
    
    print(f"Data saved to {fileName}")
    print(f"Metadata saved to {metadata_file}")
    print(f"Total samples: {total_samples} ({n_pre} pre-trigger, {n_post} post-trigger)")

    # Plot the data
    print("\nGenerating plot...")
    plot_filename = fileName.replace('.dat', '.png')
    plot_channels(result, show=True, save_filename=plot_filename)

    return


    



if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 jm_ads131m04_monitor.py
    import argparse
    defaultFileName = time.strftime('%Y%m%d-%H%M%S-trig-test.dat')
    parser = argparse.ArgumentParser(description="Jeremy's ADS131M04 trigger test")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    parser.add_argument('-f', '--file-name', metavar='fileName',
                        dest='fileName', action='store', default=defaultFileName)
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'C'
    if args.identity: node_id = args.identity
    if os.path.exists(args.fileName):
        print('File already exists; specify a new name.')
        sys.exit(1)
    sp = rs485.openPort(port_name)
    if sp:
        main(sp, node_id, args.fileName)
    print("Done.")
