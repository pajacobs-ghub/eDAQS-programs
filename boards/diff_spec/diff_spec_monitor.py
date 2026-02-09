# diff_spec_monitor.py
# Monitor the 40 differential channels and report their values.
#
# 2025-10-24 PJ Basic demonstration adapted from 2024 demo.
# 2025-10-25    Faster fetching of data.

import sys
sys.path.append("../..")
import time
import os
from comms_mcu import rs485
from comms_mcu.pic18f16q41_spectrometer_comms import PIC18F16Q41_SPECTROMETER_COMMS
from daq_mcu.avr64ea28_spi_daq import AVR64EA28_SPI_DAQ
import struct

FAST_FETCH = True
ALLOW_LED = True

def main(sp, node_id, fileName):
    print("Differential spectrometer with 40-channel DAQ board.")
    node1 = PIC18F16Q41_SPECTROMETER_COMMS(node_id, sp)
    if ALLOW_LED:
        node1.allow_LED()
    else:
        node1.suppress_LED()
    print(node1.get_version())
    avr = AVR64EA28_SPI_DAQ(node1)
    for i in range(5):
        print(f"For AVR {i}: version string = {avr.get_version(i)}")
        avr.set_ref_voltage(i, '1v024')
        avr.clear_PGA(i)
        # avr.set_PGA(i, '4X')
        avr.set_burst(i, 'ACC16')
        # avr.resume_sampling(i)
        if ALLOW_LED:
            avr.allow_LED(i)
        else:
            avr.suppress_LED(i)
        # print(f"         : register bytes = {avr.get_register_bytes(i)}")
        print(f"         : registers = {avr.get_registers_as_dict(i)}")
    #
    print(f"Start asking for data and record it to file: {fileName}")
    print("Press Control-C (KeyboardInterrupt) to stop recording.")
    f = open(fileName, 'w')
    s = struct.Struct('>40h')
    time.sleep(1.0)
    try:
        while True:
            # Note that we want the fractional part of the seconds,
            # so get the floating-point representation of time.
            t = time.time()
            stamped_text = f"{t}"
            if FAST_FETCH:
                # Fetch the analog data in a single RS485 command.
                txt = avr.fetch_all_analog_samples()
                mybytes = bytes.fromhex(txt)
                values = s.unpack_from(mybytes)
                for v in values:
                    stamped_text += " %d" % v
            else:
                # Fetch the analog data the slow way.
                for i in range(5):
                    analog_values = avr.get_sample_data(i)
                    for j in range(8):
                        stamped_text += ' %d' % analog_values[j]
            f.write(stamped_text+'\n')
            print(stamped_text)
            time.sleep(1.0) # 2026-02-09 Slow for debugging channel A9
    except KeyboardInterrupt:
        f.close()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 diff_spec_monitor.py
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
    node_id = 'D'
    if args.identity: node_id = args.identity
    if os.path.exists(args.fileName):
        print('File already exists; specify a new name.')
        sys.exit(1)
    sp = rs485.openPort(port_name)
    if sp:
        main(sp, node_id, args.fileName)
    print("Done.")
