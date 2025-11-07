# test_5_set_analog_VREF.py
# We need a voltmeter on the VREF pin of the PIC MCU.

import sys
sys.path.append("../..")
import time
from comms_mcu import rs485
from comms_mcu.pic18f16q41_comms_1_mcu import PIC18F16Q41_COMMS_1_MCU
from daq_mcu.avr64ea28_daq_mcu import AVR64EA28_DAQ_MCU

def main(sp, node_id):
    node1 = PIC18F16Q41_COMMS_1_MCU(node_id, sp)
    #
    print("Set analog VREF on PIC MCU.")
    node1.set_LED(1)
    print(node1.get_version())
    node1.set_VREF_on(64)
    time.sleep(3.0) # so we have time to see the voltmeter change
    node1.set_VREF_on(128)
    time.sleep(5.0)
    node1.set_VREF_on(0)
    node1.set_VREF_off()
    node1.set_LED(0)
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_5_set_analog_VREF.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '1'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        main(sp, node_id)
    else:
        print("Did not find the serial port.")
    print("Done.")
