# test_2_immediate_recording.py
# Make a short recording with an immediate-mode trigger.
# We have a 1kHz 20mV peak-to-peak sine wave on channels 0 and 1.
# PJ 2025-11-15, 2026-03-05 (for MCP3301 board)

import sys
sys.path.append("../..")
import time
from comms_mcu import rs485
from comms_mcu.pic18f26q71_comms_4_mcu import PIC18F26Q71_COMMS_4_MCU
from daq_mcu.pico2_daq_mcu_mcp3301 import PICO2_DAQ_MCU_MCP3301

def main(sp, node_id):
    node1 = PIC18F26Q71_COMMS_4_MCU(node_id, sp)
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
    daq_mcu = PICO2_DAQ_MCU_MCP3301(node1)
    print(daq_mcu.get_version())
    daq_mcu.set_regs_to_factory_values()
    #
    print("Make a recording.")
    node1.set_V_REF_AB(32, 32)  # should get us 0.5 volts as the ADC reference
    daq_mcu.set_sample_period_us(20)
    daq_mcu.set_nchannels(2)
    daq_mcu.set_nsamples(500)
    daq_mcu.set_trigger_immediate()
    print(daq_mcu.get_reg_values_as_text())
    print("Pico2 ready: ", node1.test_DAQ_MCU_is_ready())
    print("event has passed: ", node1.test_event_has_passed())
    daq_mcu.start_sampling()
    ready = node1.test_DAQ_MCU_is_ready()
    while not ready:
        print('Waiting...')
        time.sleep(0.1)
        ready = node1.test_DAQ_MCU_is_ready()
    print("event has passed: ", node1.test_event_has_passed())
    if daq_mcu.did_not_keep_up_during_sampling():
        print("Failed to keep pace during sampling.")
    else:
        print("Sampling kept pace ok.")
    print(f"V_REF_AB {daq_mcu.analog_millivolts()} mV")
    nchan = daq_mcu.get_nchannels()
    nsamples = daq_mcu.get_nsamples()
    mode = daq_mcu.get_trigger_mode()
    print(f"nchan={nchan}, nsamples={nsamples}, trigger_mode={mode}")
    print("About to fetch data...")
    start = time.time()
    my_data = daq_mcu.get_recorded_data()
    # print("my_data=", my_data)
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch {nsamples} sample sets")
    #
    print("With that recorded data, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1) = plt.subplots(2,1)
    ax0.set_title('Pico2+MCP3301 eDAQS sampled data')
    ax0.plot(my_data[0]); ax0.set_ylabel('chan 0')
    ax1.plot(my_data[1]); ax1.set_ylabel('chan 1')
    ax1.set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_2_immediate_recording.py -i F
    import argparse
    parser = argparse.ArgumentParser(description="eDAQS node test program")
    parser.add_argument('-p', '--port', dest='port', help='name for serial port')
    parser.add_argument('-i', '--identity', dest='identity', help='single-character identity')
    args = parser.parse_args()
    port_name = '/dev/ttyUSB0'
    if args.port: port_name = args.port
    node_id = 'F'
    if args.identity: node_id = args.identity
    sp = rs485.openPort(port_name)
    if sp:
        main(sp, node_id)
    else:
        print("Did not find the serial port.")
    print("Done.")
