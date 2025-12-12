# x2_photodiode_recorder.py
# Make a recording of photodiode signals with a wait-for-event trigger,
# then fetch the recorded data, unpack the samples, save them and plot them.
# PJ 2025-12-12.

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
    daq_mcu.set_nsamples(16000-4000) # number of samples after trigger event
    daq_mcu.set_trigger_wait_for_eventn()
    print(daq_mcu.get_reg_values_as_text())
    #
    print("Monitor chan 0 analog voltage for trigger event.")
    node1.enable_internal_trigger(189, 1)
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
    my_data = daq_mcu.fetch_SRAM_data(n_select=16000, n_pretrigger=4000)
    # print("my_data=", my_data)
    elapsed = time.time() - start
    print(f"{elapsed:.2f} seconds to fetch {nsamples} sample sets")
    my_samples = daq_mcu.unpack_to_samples(my_data)
    N = my_samples['nsamples_select']
    print(f"Reference voltage {my_samples['ref_voltage']}")
    #
    with open('x2-samples.metadata', 'wt') as f:
        f.write(f'nsamples_select: {N}\n')
        f.write(f'nchan: {nchan}\n')
        f.write(f'nsamples_select_pretrigger: {my_samples["nsamples_select_pretrigger"]}\n')
        f.write(f'trigger_mode: {my_samples["trigger_mode"]}\n')
        f.write(f'dt_us: {my_samples["dt_us"]}\n')
        f.write(f'late_flag: {my_samples["late_flag"]}\n')
        f.write(f'analog_gain: {my_samples["analog_gain"]}\n')
        f.write(f'ref_voltage: {my_samples["ref_voltage"]}\n')
    with open('x2-samples.data', 'wt') as f:
        hdr = f't(us) chan[0]' # Assuming 1us sample period
        for j in range(1,nchan): hdr += f' chan[{j}]'
        hdr += '\n'
        f.write(hdr);
        for i in range(N):
            f.write('%g %d' % (i, my_samples['data'][0][i]))
            for j in range(1,nchan): f.write(' %d' % my_samples['data'][j][i])
            f.write('\n')
    print("With the post-trigger samples, make a plot.")
    import matplotlib.pyplot as plt
    fig, (ax0,ax1,ax2) = plt.subplots(3,1)
    ax0.set_title('Pico2+BU79100G eDAQS sampled data')
    ax0.plot(my_samples['data'][0][0:N]); ax0.set_ylabel('diodeAx11')
    ax1.plot(my_samples['data'][1][0:N]); ax1.set_ylabel('diodeA')
    ax2.plot(my_samples['data'][2][0:N]); ax2.set_ylabel('diodeB')
    ax2.set_xlabel('sample number')
    plt.show()
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 x2_photodiode_recorder.py -i E
    import argparse
    parser = argparse.ArgumentParser(description="X2 transient recorder program")
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
