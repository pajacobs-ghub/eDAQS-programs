# diff_spect_proto.py
# Set up three differential channels and report their values.
# 2024-08-06 PJ Basic demonstration.

from rs485_edaq import *

def main(sp, node_id):
    node1 = EDAQSNode(node_id, sp)
    #
    print("Differential spectrometer prototype.")
    print(node1.get_PIC_version())
    if not node1.test_DAQ_MCU_is_ready():
        print("Reset DAQ_MCU")
        node1.reset_DAQ_MCU()
        time.sleep(2.0)
    node1.flush_rx2_buffer()
    daq_mcu = AVR64EA28_DAQ_MCU(node1)
    print(daq_mcu.get_AVR_version())
    #
    daq_mcu.clear_AVR_PGA()
    daq_mcu.set_AVR_analog_ref_voltage('1v024')
    daq_mcu.set_AVR_analog_channels([('AIN0','AIN1'),
                                     ('AIN2','AIN3'),
                                     ('AIN4','AIN5')])
    daq_mcu.set_AVR_sample_period_us(1000)
    daq_mcu.set_AVR_nsamples(10)
    daq_mcu.set_AVR_trigger_immediate()
    # print(daq_mcu.get_AVR_reg_values_as_text())
    print("AVR ready: ", node1.test_DAQ_MCU_is_ready())
    print("event has passed: ", node1.test_event_has_passed())
    daq_mcu.start_AVR_sampling()
    ready = node1.test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting...')
        time.sleep(0.01)
        ready = node1.test_DAQ_MCU_is_ready()
    # After sampling is done.
    print("event has passed: ", node1.test_event_has_passed())
    nchan = daq_mcu.get_AVR_nchannels()
    nsamples = daq_mcu.get_AVR_nsamples()
    for i in range(nsamples):
        items = daq_mcu.get_AVR_formatted_sample(i)
        print(items)
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 diff_spect_proto.py
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
