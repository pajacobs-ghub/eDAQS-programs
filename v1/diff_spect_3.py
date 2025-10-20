# diff_spect_3.py
# Set up 16 differential channels and report their values.
# 2024-08-06 PJ Basic demonstration.
# 2024-08-15    Some convenience for playing with the hardware.
# 2024-08-25    Use three nodes as installed on David's rig.

import sys
import os
import time
from rs485_edaq import *

channels = {'5': [('AIN28','AIN29'), ('AIN30','AIN31'), ('AIN0','AIN1'),
                  ('AIN2','AIN3'), ('AIN4','AIN5'), ('AIN6','AIN7')],
            '6': [('AIN28','AIN29'), ('AIN30','AIN31'), ('AIN0','AIN1'),
                  ('AIN2','AIN3'), ('AIN4','AIN5'), ('AIN6','AIN7')],
            '7': [('AIN28','AIN29'), ('AIN30','AIN31'), ('AIN0','AIN1'),
                  ('AIN2','AIN3')],}

def main(sp, node_ids, fileName):
    print("Differential spectrometer with 3 eDAQS boards.")
    assert len(node_ids) == 3, "Expected 3 id characters"
    ids = [node_ids[0], node_ids[1], node_ids[2]]
    nodes = {}
    daq_mcus = {}
    for myid in ids:
        nodes[myid] = EDAQSNode(myid, sp)
        node = nodes[myid]
        print(node.get_PIC_version())
        if not node.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node.reset_DAQ_MCU()
            time.sleep(2.0)
        node.flush_rx2_buffer()
        daq_mcu = AVR64EA28_DAQ_MCU(node)
        print(daq_mcu.get_AVR_version())
        daq_mcus[myid] = daq_mcu
        #
        daq_mcu.clear_AVR_PGA()
        # daq_mcu.set_AVR_PGA('8X')
        daq_mcu.set_AVR_analog_ref_voltage('4v096')
        # daq_mcu.set_AVR_analog_ref_voltage('1v024')
        daq_mcu.set_AVR_analog_channels(channels[myid])
        # daq_mcu.set_AVR_burst('NONE')
        daq_mcu.set_AVR_burst('ACC16')
    #
    # Start asking for data and recording it to a file.
    f = open(fileName, 'w')
    try:
        while True:
            text0 = daq_mcus[ids[0]].immediate_AVR_sample_set().strip()
            text1 = daq_mcus[ids[1]].immediate_AVR_sample_set().strip()
            text2 = daq_mcus[ids[2]].immediate_AVR_sample_set().strip()
            # Note that we want the fractional part of the seconds,
            # so get the floating-point representation of time.
            t = time.time()
            stamped_text = f"{text0} {text1} {text2} {t}"
            f.write(stamped_text+'\n')
            print(stamped_text)
            time.sleep(0.2)
    except KeyboardInterrupt:
        f.close()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 diff_spect_proto.py
    import argparse
    defaultFileName = time.strftime('%Y%m%d-%H%M%S-diff-spectrometer.dat')
    parser = argparse.ArgumentParser(description="Differential spectrometer 3-boards",
                                     epilog='Once started, use KeyboardInterrupt (Ctrl-C) to stop.')
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identities', dest='identities', help='3 times single-character identity')
    parser.add_argument('-f', '--file-name', metavar='fileName',
                        dest='fileName', action='store', default=defaultFileName)
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_ids = '567'
    if args.identities: node_ids = args.identities
    if os.path.exists(args.fileName):
        print('file already exists; specify a new name')
        sys.exit(1)
    sp = openPort(port_name)
    if sp:
        main(sp, node_ids, args.fileName)
    else:
        print("Did not find the serial port.")
        print(f'Did not find serial port: {args.serialPort}')
        print('Serial ports that can be seen:')
        import serial.tools.list_ports as list_ports
        print([p.device for p in list_ports.comports()])
        sys.exit(1)
    print("Done.")
