# test_1_analog_voltages.py

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Let us set and read some analog voltages.")
    node1.set_PIC_LED(1)
    print(node1.get_PIC_version())
    # If we have been reprogramming the AVR while the PIC18 is running,
    # we will likely have rubbish characters in the PIC18's RX2 buffer.
    node1.flush_rx2_buffer()
    daq_mcu = AVR64EA28_DAQ_MCU(node1)
    print(daq_mcu.get_AVR_version())
    #
    print("Exercise the software trigger line.")
    node1.assert_event_line_low()
    time.sleep(2) # to let the DVM register the voltage levels
    node1.release_event_line()
    time.sleep(2)
    #
    print("Look at the current analog voltages.")
    daq_mcu.clear_AVR_PGA()
    daq_mcu.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
    daq_mcu.print_AVR_reg_values()
    for i in range(5):
        print('analog values=', daq_mcu.immediate_AVR_sample_set())
        time.sleep(0.5)
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_1_analog_voltages.py -i 2
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = '1'
    if args.identity: node_id = args.identity
    sp = openPort(port_name)
    if sp:
        main(sp, node_id)
    else:
        print("Did not find the serial port.")
    print("Done.")
