# test_1_analog_voltages.py

from rs485_edaq import *

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Let us set and read some analog voltages.")
        node1.set_PIC_LED(1)
        print(node1.get_PIC_version())
        # If we have been reprogramming the AVR while the PIC18 is running,
        # we will likely have rubbish characters in the PIC18's RX2 buffer.
        node1.flush_rx2_buffer()
        print(node1.get_AVR_version())
        #
        print("Exercise the software trigger line.")
        node1.assert_event_line_low()
        time.sleep(2) # to let the DVM register the voltage levels
        node1.release_event_line()
        time.sleep(2)
        #
        print("Look at the current analog voltages.")
        node1.clear_AVR_PGA()
        node1.set_AVR_analog_channels([('AIN28','GND'),('ain29','gnd')])
        node1.print_AVR_reg_values()
        for i in range(5):
            print('analog values=', node1.immediate_AVR_sample_set())
            time.sleep(0.5)
    else:
        print("Did not find the serial port.")
    print("Done.")
