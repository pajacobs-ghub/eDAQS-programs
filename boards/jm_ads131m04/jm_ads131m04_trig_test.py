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
import struct

NSELECT = 4000  # number of samples to fetch after the trigger
NPRETRIGGER = 2000  # number of samples to fetch before the trigger

def main(sp, node_id, fileName):
    print(" =====================================")
    print(" SUPER-ADC ADS131M04 TRIGGER TEST.")
    print(" version 2025-11-10 JM")
    print(" =====================================")
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
    daq.set_num_samples(1024)  # 24 samples per channel
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
    while not node.test_event_has_passed():
        print("Waiting for trigger...")
        time.sleep(1.0)
    print("After trigger, result of Q command:", node.command_COMMS_MCU('Q'))

    # Even though event has passed, the DAQ_MCU may be still sampling.
    ready = node.test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting for DAQ_MCU...')
        time.sleep(0.1)
        ready = node.test_DAQ_MCU_is_ready()
    print("After waiting for DAQ, result of Q command:", node.command_COMMS_MCU('Q'))

    node.disable_external_trigger()
    daq.error_flags()
    node.set_LED(0)

    # After sampling completes
    result = daq.fetch_SRAM_data(n_pretrigger=256)

    # Access the data
    data_bytes = result['data']
    n_pre = result['nsamples_before_trigger']
    n_post = result['nsamples_after_trigger']
    total_samples = n_pre + n_post

    # Reconstruct samples (each sample = 16 bytes)
    for i in range(total_samples):
        offset = i * 16
        ch0, ch1, ch2, ch3 = struct.unpack('<4i', data_bytes[offset:offset+16])
        #print(f"Sample {i}: [{ch0}, {ch1}, {ch2}, {ch3}]")

    return


    



if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 jm_ads131m04_monitor.py
    import argparse
    defaultFileName = time.strftime('%Y%m%d-%H%M%S-diff-spectrometer.dat')
    parser = argparse.ArgumentParser(description="Differential spectrometer 3-boards",
                                     epilog='Once started, use KeyboardInterrupt (Ctrl-C) to stop.')
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