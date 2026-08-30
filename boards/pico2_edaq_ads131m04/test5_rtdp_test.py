# test5_rtdp_test.py
# This script is specific to Jeremy's "SUPER-ADC ADS131M04" board, either Revision B or C,
# and designed to work in conjuction with a FADEC board to access the Real Time Data Port
#
# JM 2026-02-25   First pass, FADEC board of choice is Jeremy's "super-fadec-preemptrt"
#                 manufactured in December 2025 based on a Raspberry Pi 4B

import sys
sys.path.append("../..")
import time
import os
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
from daq_mcu.pico2_daq_mcu_ads131m04 import PICO2_ADS131M04_DAQ
from plot_function import plot_channels
import struct

NSAMPLES = 12288

def main(sp, node_id):
    print("\n =====================================")
    print(" SUPER-ADC ADS131M04 RTDP TEST.")
    print(" version 2026-02-25 JM")
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
    daq.set_osr(128) # OSR 128 @ 8192 kHz CLKIN = 32 kHz sample rate
    daq.set_trigger_mode(2)  # external trigger, but tied to PICO2-EVENT# line
    daq.set_num_samples(NSAMPLES)  # samples per channel
    daq.clear_data_array() # clear the buffer
    print("DAQ_MCU ready: ", node.test_DAQ_MCU_is_ready())
    time.sleep(0.1)
    print("Maximum number of samples storable in SRAM:", node.command_DAQ_MCU('m'))

    # Make sure that PIC has not been asked to hold SYS-EVENT# low.
    node.release_event_line()
    node.disable_external_trigger()
    
    # enable RTDP
    #daq.set_RTDP_debug_mode(0) # Enable RTDP debug mode, which just sends 9999 to master instead of ADC
    daq.set_RTDP_timeout_us(1000) # 1 ms timeout: firmware minimum is 100 µs; actual 20 MHz
                                  # SPI transfer of 16 bytes takes ~10 µs, so 1 ms is valid.

    # tell the DAQ to start its sampling process
    daq.sample()  # Start sampling process
    node.set_LED(1)  # Turn on LED to indicate sampling

    # Hold indefinitely until user kills the process (Ctrl-C).
    # On KeyboardInterrupt perform minimal cleanup and exit.
    try:
        print("Sampling started — holding indefinitely. Press Ctrl-C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nUser requested exit. Cleaning up and exiting.")
        try:
            node.disable_external_trigger()
        except Exception:
            pass
        try:
            daq.error_flags()
        except Exception:
            pass
        try:
            node.set_LED(0)
        except Exception:
            pass
        try:
            node.release_event_line()
        except Exception:
            pass
        return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 jm_ads131m04_monitor.py
    import argparse
    parser = argparse.ArgumentParser(description="Jeremy's ADS131M04 trigger test")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')

    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'C'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        main(sp, node_id)
    print("Done.")
