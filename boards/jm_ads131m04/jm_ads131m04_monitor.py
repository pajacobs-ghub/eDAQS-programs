# jm_ads131m04_monitor.py
# This script is specific to Jeremy's "SUPER-ADC ADS131M04" board, either Revision B or C.
# Monitor 2 differential channels and report their values.
#
# 2025-11-05    First pass, adapted from diff_spec_monitor.py.

import sys
sys.path.append("../..")
import time
import os
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
from comms_mcu.pic18f16q41_comms_1_mcu import PIC18F16Q41_COMMS_1_MCU
from daq_mcu.pico2_ads131m04 import PICO2_ADS131M04_DAQ

import struct

FAST_FETCH = True

def main(sp, node_id, fileName):
    print("SUPER-ADC ADS131M04 board monitor.")
    node1 = PIC18F16Q41_JM_ADS131M04_COMMS(node_id, sp)
    daq = PICO2_ADS131M04_DAQ(node1)
    print(node1.get_version())
    #node1.reset_DAQ_MCU()
    #time.sleep(2)
    print(daq.get_version())
    print(daq.reset_registers())
    
    # Get raw ADC codes
    codes = daq.single_sample_as_ints()
    print(f"Raw codes: {codes}")

    # Convert to voltages with default settings (1.2V ref, gain=1)
    voltages = daq.single_sample_as_volts()
    print(f"Voltages: {voltages}")



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