# test_6_external_trigger.py
# Need to provide an analog voltage on the ext-trig input.

from rs485_edaq import *

if __name__ == '__main__':
    sp = openPort('/dev/ttyUSB0')
    if sp:
        node1 = EDAQSNode('1', sp)
        #
        print("Test the external-trigger input on PIC.")
        node1.set_PIC_LED(1)
        print(node1.get_PIC_version())
        # Have put in the AVR reset so that previous testing
        # that involved recording and the AVR pulling active-low EVENT#
        # does not pre-trigger this test.
        node1.reset_AVR()
        time.sleep(2.0)
        # Make sure that PIC has not been asked to hole EVENT# low.
        node1.release_event_line()
        node1.disable_external_trigger()
        #
        print("Before enabling trigger, result of Q command:", node1.command_PIC('Q'))
        node1.enable_external_trigger(128, 'pos')
        while not node1.test_event_has_passed():
            print("Waiting...")
            time.sleep(1.0)
        print("After trigger, result of Q command:", node1.command_PIC('Q'))
        node1.disable_external_trigger()
        node1.set_PIC_LED(0)
    else:
        print("Did not find the serial port.")
    print("Done.")
