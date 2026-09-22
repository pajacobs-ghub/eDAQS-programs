// file: avr64ea28_daq_mcu.go
// Service functions for the AVR64EA28 DAQ MCU.
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package edaqs

import (
	_ "bufio"
	_ "bytes"
	_ "fmt"
	_ "go.bug.st/serial"
	_ "log"
)

type AVR_DAQ_MCU struct {
	comms_mcu *COMMS_1_MCU
}

func NewAVR_DAQ_MCU(comms_mcu *COMMS_1_MCU) *AVR_DAQ_MCU {
	return &AVR_DAQ_MCU{
		comms_mcu: comms_mcu,
	}
}

func (my *AVR_DAQ_MCU) GetVersion() (resp []byte, err error) {
	resp, err = my.comms_mcu.command_DAQ_MCU([]byte("v"))
	return
}
