# diff_spect_proto.py
# Set up three differential channels and report their values.
# 2024-08-06 PJ Basic demonstration.
# 2024-08-15    Some convenience for playing with the hardware.

import sys
import os
import time
from rs485_edaq import *

def main(sp, node_id, fileName):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Differential spectrometer prototype.")
    print(node1.get_PIC_version())
    if not node1.test_DAQ_MCU_is_ready():
        print("Reset DAQ_MCU")
        node1.reset_DAQ_MCU()
        time.sleep(2.0)
    node1.flush_rx2_buffer()
    daq_mcu = AVR64EA28_DAQ_MCU(node1)
    print(daq_mcu.get_AVR_version())
    #
    daq_mcu.clear_AVR_PGA()
    # daq_mcu.set_AVR_PGA('8X')
    daq_mcu.set_AVR_analog_ref_voltage('4v096')
    # daq_mcu.set_AVR_analog_ref_voltage('1v024')
    daq_mcu.set_AVR_analog_channels([('AIN0','AIN1'),
                                     ('AIN2','AIN3'),
                                     ('AIN4','AIN5')])
    # daq_mcu.set_AVR_burst('NONE')
    daq_mcu.set_AVR_burst('ACC16')
    # Start asking for data and recording it to a file.
    f = open(fileName, 'w')
    try:
        while True:
            text = daq_mcu.immediate_AVR_sample_set().strip()
            # Note that we want the fractional part of the seconds,
            # so get the floating-point representation of time.
            t = time.time()
            stamped_text = f"{text} {t}"
            f.write(stamped_text+'\n')
            print(stamped_text)
            time.sleep(0.5)
    except KeyboardInterrupt:
        f.close()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 diff_spect_proto.py
    import argparse
    defaultFileName = time.strftime('%Y%m%d-%H%M%S-diff-spectrometer.dat')
    parser = argparse.ArgumentParser(description="eDAQS node test program",
                                     epilog='Once started, use KeyboardInterrupt (Ctrl-C) to stop.')
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    parser.add_argument('-f', '--file-name', metavar='fileName',
                        dest='fileName', action='store', default=defaultFileName)
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '1'
    if args.identity: node_id = args.identity
    if os.path.exists(args.fileName):
        print('file already exists; specify a new name')
        sys.exit(1)
    sp = openPort(port_name)
    if sp:
        main(sp, node_id, args.fileName)
    else:
        print("Did not find the serial port.")
        print(f'Did not find serial port: {args.serialPort}')
        print('Serial ports that can be seen:')
        import serial.tools.list_ports as list_ports
        print([p.device for p in list_ports.comports()])
        sys.exit(1)
    print("Done.")
