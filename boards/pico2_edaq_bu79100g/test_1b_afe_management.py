# test_1b_afe_management.py
# Exercises the PIC18F26Q71 AFE-management interface which includes
#   some GPIO pins
#   SPI communication
#   I2C communication.
#
# We run this test with
#   a TC74A0 temperature sensor attached to the I2C interface
#   and a LED attached to the RA7 GPIO pin.
#
# PJ 2026-03-13
#    2026-03-22 Adapt to Pico2+BU79100G recording board.

import sys
sys.path.append("../..")
import time
from comms_mcu import rs485
from comms_mcu.pic18f26q71_comms_3_mcu import PIC18F26Q71_COMMS_3_MCU

def main(sp, node_id):
    node1 = PIC18F26Q71_COMMS_3_MCU(node_id, sp)
    #
    print("Test the analog-front-end management interface on the PIC MCU.")
    print(node1.get_version())
    # Have put in the Pico2 reset so that previous testing
    # that involved recording and the Pico2 pulling active-low EVENT#
    # does not pre-trigger this test.
    node1.reset_DAQ_MCU()
    time.sleep(2.0)
    # Make sure that PIC has not been asked to hold EVENT# low.
    node1.disable_hardware_trigger()
    node1.release_event_line()
    print("Result of Q command:", node1.command_COMMS_MCU('Q'))
    #
    print("Turn on LED attached to RA7.")
    # bits                                      decimal
    #    7    6    5    4    3    2    1    0    value
    #    X    X    X    X  RA6  RA5  RA4  RA3          <== PCB Revision 1
    #    X    X    X    X  RA7  RA6  RA5  RA4          <== PCB Revision 2
    #    0    0    0    0    0    1    1    1  ==  7
    #    0    0    0    0    1    0    0    0  ==  8
    node1.utility_pins_write_ANSEL(7) # Last pin as digital; others analog
    node1.utility_pins_write_TRIS(7) # Last pin as output; others input
    node1.utility_pins_write_LAT(8) # set Last pin high to turn LED on
    time.sleep(1.0)
    node1.utility_pins_write_LAT(0) # turn LED off
    #
    try:
        print("I2C bytes read:", node1.i2c_read(72, 1), " expect room temperature in degrees C")
        print("I2C bytes written:", node1.i2c_write(72, [1,]))
        print("I2C bytes read:", node1.i2c_read(72, 1), " expect 64 as content of status register")
        print("I2C bytes written:", node1.i2c_write(72, [0,]))
        print("I2C bytes read:", node1.i2c_read(72, 1), " expect room temperature again")
    except Exception as err:
        print(f"Problem with I2C communication: {err}")
    #
    try:
        print("SPI init:", node1.spi_init(3, 1, 0, 0))
        print("SPI exchange:", node1.spi_exchange([0, 1, 2, 3]))
        print("SPI close:", node1.spi_close())
    except Exception as err:
        print(f"Problem with SPI communication: {err}")
    #
    return

if __name__ == '__main__':
    # Typical use on a Linux box:
    # $ python3 test_1b_read_and_write_i2c.py -i E
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
