# test_6_external_trigger.py
# Need to provide an analog voltage on the ext-trig input.

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Test the external-trigger input on PIC.")
    node1.set_PIC_LED(1)
    print(node1.get_PIC_version())
    # Have put in the AVR reset so that previous testing
    # that involved recording and the AVR pulling active-low EVENT#
    # does not pre-trigger this test.
    node1.reset_DAQ_MCU()
    time.sleep(2.0)
    # Make sure that PIC has not been asked to hold EVENT# low.
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
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_6_external_trigger.py -i 2
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
