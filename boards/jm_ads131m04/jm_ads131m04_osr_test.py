# jm_ads131m04_osr_test.py
# This script is specific to Jeremy's "SUPER-ADC ADS131M04" board, either Revision B or C.
# Sweep through various OSR settings and verify no error flags are set.
#
# 2025-11-05    First pass, adapted from diff_spec_monitor.py.
# 2025-11-09    Added OSR sweep test.

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
    print(node1.get_version())
    #node1.reset_DAQ_MCU()
    #time.sleep(2)
    print(daq.get_version())
    print(daq.set_clk(8192))  # Set clock to 8192 kHz

    # SWEEP through all OSR values
    print("\n=== OSR Sweep Test ===")
    osr_values = [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16256]
    
    for osr in osr_values:
        print(f"\nTesting OSR={osr}...")
        result = daq.set_osr(osr)
        print(f"  Set OSR: {result}")
        
        # Get raw ADC codes
        codes = daq.single_sample_as_ints()
        print(f"  Raw codes: {codes}")
        
        # Check error flags
        errors = daq.error_flags()
        print(f"  Error flags: {errors} (type: {type(errors)})")
        
        if int(errors) != 0:
            print(f"  *** ERROR: Non-zero error flag ({errors}) for OSR={osr}! ***")
        else:
            print(f"  ✓ OSR={osr} passed")
    
    print("\n=== OSR Sweep Test Complete ===")
    
    # Reset to default OSR
    print("\nResetting to OSR=1024...")
    print(daq.set_osr(1024))
    
    # Get raw ADC codes
    codes = daq.single_sample_as_ints()
    print(f"Raw codes: {codes}")

    # print error flags
    errors = daq.error_flags()
    print(f"Error flags: {errors}")



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