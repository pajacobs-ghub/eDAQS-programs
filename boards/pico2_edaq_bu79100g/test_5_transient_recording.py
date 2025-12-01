# test_5_transient_recording.py
# Make a short recording with a wait-for-event trigger,
# then fetch the whole blob of memory and unpack the samples.
# We have a 1kHz sine wave on channels 0 and 1.
# PJ 2025-11-15, 2025-11-16 1MSps demo.

import sys
sys.path.append("../..")
import time
from comms_mcu import rs485
from comms_mcu.pic18f26q71_comms_3_mcu import PIC18F26Q71_COMMS_3_MCU
from daq_mcu.pico2_daq_mcu_bu79100g import PICO2_DAQ_MCU_BU79100G

def main(sp, node_id):
    node1 = PIC18F26Q71_COMMS_3_MCU(node_id, sp)
    #
    print("Example of a recording with plot of collected data.")
    print(node1.get_version())
    # Have put in the Pico2 reset so that previous testing
    # that involved recording and the Pico2 pulling active-low EVENT#
    # does not pre-trigger this test.
    node1.reset_DAQ_MCU()
    time.sleep(2.0)
    # Make sure that PIC has not been asked to hold EVENT# low.
    node1.disable_hardware_trigger()
    node1.release_event_line()
    node1.flush_rx2_buffer()
    #
    daq_mcu = PICO2_DAQ_MCU_BU79100G(node1)
    print(daq_mcu.get_version())
    daq_mcu.set_regs_to_factory_values()
    #
    print("Prepare to make a recording.")
    daq_mcu.set_sample_period_us(1)
    daq_mcu.set_nsamples(2000)
    daq_mcu.set_trigger_wait_for_eventn()
    print(daq_mcu.get_reg_values_as_text())
    #
    print("Monitor chan 0 analog voltage for trigger event.")
    node1.enable_internal_trigger(64, 1)
    if node1.test_event_has_passed():
        print("Event has passed before we started sampling; quitting script.")
        return
    #
    print("Pico2 ready: ", node1.test_DAQ_MCU_is_ready())
    daq_mcu.start_sampling()
    ready = node1.test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting...')
        time.sleep(0.1)
        ready = node1.test_DAQ_MCU_is_ready()
    print("event has passed: ", node1.test_event_has_passed())
    nchan = daq_mcu.get_nchannels()
    nsamples = daq_mcu.get_nsamples()
    mode = daq_mcu.get_trigger_mode()
    print(f"nchan={nchan}, nsamples={nsamples}, trigger_mode={mode}")
    print("About to fetch data...")
    start = time.time()
    my_data = daq_mcu.fetch_SRAM_data(n_select=2500, n_pretrigger=500)
    # print("my_data=", my_data)
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch {nsamples} sample sets")
    my_samples = daq_mcu.unpack_to_samples(my_data)
    print(f"Reference voltage {my_samples['ref_voltage']}")
    #
    print("With the post-trigger samples, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1) = plt.subplots(2,1)
    ax0.set_title('Pico2+BU79100G eDAQS sampled data')
    N = my_samples['nsamples_select'] # IMMEDIATE_MODE recording
    ax0.plot(my_samples['data'][0][0:N]); ax0.set_ylabel('chan 0')
    ax1.plot(my_samples['data'][1][0:N]); ax1.set_ylabel('chan 1')
    ax1.set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_6_internal_trigger.py -i E
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'E'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        main(sp, node_id)
    else:
        print("Did not find the serial port.")
    print("Done.")
