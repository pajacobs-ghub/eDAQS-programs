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

FAST_FETCH = True

def main(sp, node_id, fileName):
    print("SUPER-ADC ADS131M04 board monitor.")
    node1 = PIC18F16Q41_JM_ADS131M04_COMMS(node_id, sp)
    daq = PICO2_ADS131M04_DAQ(node1)

    # Get versions, and reset DAQ_MCU
    print(node1.get_version())
    node1.reset_DAQ_MCU()
    time.sleep(1.6)
    print(daq.get_version())

    # Configure ADS131M04
    print(daq.set_clk(8192))  # Set clock to 8192 kHz
    daq.set_osr(1024) # Default OSR
    daq.set_trigger_mode(2)  # External trigger
    daq.set_num_samples(24)  # 24 samples per channel
    print("DAQ_MCU ready: ".format(node1.test_DAQ_MCU_is_ready()))

    # Make sure that PIC has not been asked to hold EVENT# low.
    node1.release_event_line()
    node1.disable_external_trigger()
    #
    print("Before enabling trigger, result of Q command:", node1.command_COMMS_MCU('Q'))
    node1.enable_external_trigger(64, 'pos')
    daq.sample()  # Start sampling process
    node1.set_LED(1)
    while not node1.test_event_has_passed():
        print("Waiting...")
        print(node1.command_COMMS_MCU('a'))
        time.sleep(1.0)
    print("After trigger, result of Q command:", node1.command_COMMS_MCU('Q'))
    node1.disable_external_trigger()
    node1.set_LED(0)
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