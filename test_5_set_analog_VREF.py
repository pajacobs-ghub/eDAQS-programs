# test_5_set_analog_VREF.py
# We need a voltmeter on the VREF pin of the PIC MCU.

from rs485_edaq import *

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Set analog VREF on PIC MCU.")
        node1.set_PIC_LED(1)
        print(node1.get_PIC_version())
        node1.set_PIC_VREF_on(64)
        time.sleep(3.0) # so we have time to see the voltmeter change
        node1.set_PIC_VREF_on(128)
        time.sleep(5.0)
        node1.set_PIC_VREF_on(0)
        node1.set_PIC_VREF_off()
        node1.set_PIC_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
