# usq_monitor.py
# Monitor the ADC channel values on each of two boards, nodes '8' and '9'.
# PJ 2024-11-15
#

from rs485_edaq import *

def main(sp, node_ids):
    nboards = len(node_ids)
    nodes = [EDAQSNode(node_ids[j], sp) for j in range(nboards)]
    #
    print("Monitor ADC values indefinitely.")
    for node in nodes:
        print(node.get_PIC_version())
        if not node.test_DAQ_MCU_is_ready():
            print("Reset DAQ_MCU")
            node.reset_DAQ_MCU()
            time.sleep(2.0)
        node.flush_rx2_buffer()
        # Make sure that PIC has not been asked to hold EVENT# low.
        node.release_event_line()
        node.disable_external_trigger()
    daq_mcus = [AVR64EA28_DAQ_MCU(node) for node in nodes]
    for daq_mcu in daq_mcus:
        print(daq_mcu.get_AVR_version())
    #
    # The following lines are specifically for Jeremy's wiring arrangement.
    daq_mcus[0].set_AVR_analog_channels([('AIN4','GND'),('AIN0','GND'),('AIN1','GND'),
                                         ('AIN2','GND'),('AIN3','GND'),('AIN7','GND')])
    daq_mcus[1].set_AVR_analog_channels([('AIN4','GND'),('AIN0','GND'),('AIN6','GND'),
                                         ('AIN2','GND'),('AIN3','GND'),('AIN7','GND')])
    for daq_mcu in daq_mcus:
        daq_mcu.set_AVR_analog_ref_voltage('4v096')
        daq_mcu.clear_AVR_PGA()
        daq_mcu.set_AVR_burst(0)
    #
    print("Press Control-C to finish.")
    try:
        while True:
            responses = [daq_mcus[j].immediate_AVR_sample_set() for j in range(nboards)]
            # Note that we manually format the line of text below to make it easy to read.
            # If you change the number of boards, this format will need to change also.
            print(f'board={node_ids[0]}: {responses[0]}    board={node_ids[1]}: {responses[1]}')
            time.sleep(1.0)
    except KeyboardInterrupt:
        print('Done.')
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 usq_monitor.py
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    # The following list of node identities needs to match your arrangement of boards.
    node_ids = ['8', '9']
    sp = openPort(port_name)
    if sp:
        main(sp, node_ids)
    else:
        print("Did not find the serial port.")
    print("Done.")
