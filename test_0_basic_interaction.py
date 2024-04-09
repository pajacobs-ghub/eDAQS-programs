# test_0_basic_interaction.py

from rs485_edaq import *

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Basic interaction with both MCUs.")
        node1.set_PIC_LED(1)
        print(node1.get_PIC_version())
        # If we have been reprogramming the AVR while the PIC18 is running,
        # we will likely have rubbish characters in the PIC18's RX2 buffer.
        node1.flush_rx2_buffer()
        print(node1.get_AVR_version())
        print(node1.get_AVR_reg(0))
        print(node1.set_AVR_reg(0, 250))
        print(node1.get_AVR_reg(0))
        node1.set_AVR_regs_to_factory_values()
        node1.set_AVR_regs_from_dict({1:6, 2:100})
        node1.print_AVR_reg_values()
        time.sleep(1.0)
        node1.set_PIC_LED(0)
        for i in range(2):
            time.sleep(0.5)
            node1.set_PIC_LED(1)
            time.sleep(0.5)
            node1.set_PIC_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
