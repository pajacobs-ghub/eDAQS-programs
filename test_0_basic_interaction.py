# test_0_basic_interaction.py

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Basic interaction with both MCUs.")
    node1.set_PIC_LED(1)
    print(node1.get_PIC_version())
    # If we have been reprogramming the AVR while the PIC18 is running,
    # we will likely have rubbish characters in the PIC18's RX2 buffer.
    node1.flush_rx2_buffer()
    daq_mcu = AVR64EA28_DAQ_MCU(node1)
    print(daq_mcu.get_AVR_version())
    print(daq_mcu.get_AVR_reg(0))
    print(daq_mcu.set_AVR_reg(0, 250))
    print(daq_mcu.get_AVR_reg(0))
    daq_mcu.set_AVR_regs_to_factory_values()
    daq_mcu.set_AVR_regs_from_dict({1:6, 2:100})
    daq_mcu.print_AVR_reg_values()
    time.sleep(1.0)
    node1.set_PIC_LED(0)
    for i in range(2):
        time.sleep(0.5)
        node1.set_PIC_LED(1)
        time.sleep(0.5)
        node1.set_PIC_LED(0)
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_0_basic_interaction.py -i 2
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
