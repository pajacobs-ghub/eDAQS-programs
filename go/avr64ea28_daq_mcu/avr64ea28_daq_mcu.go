// file: avr64ea28_daq_mcu.go
// Service functions for the AVR64EA28 DAQ MCU.
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package avr64ea28_daq_mcu

import (
	_ "bufio"
	_ "bytes"
	"fmt"
	_ "go.bug.st/serial"
	_ "log"
	comms "example.com/edaqs/pic18f16q41_comms_1"
)


type AVR_DAQ_MCU struct {
	comms_mcu *comms.COMMS_1_MCU
}

func NewAVR_DAQ_MCU(comms_mcu *comms.COMMS_1_MCU) *AVR_DAQ_MCU {
	return &AVR_DAQ_MCU{
		comms_mcu: comms_mcu,
	}
}

func (my *AVR_DAQ_MCU) GetVersion() (resp []byte, err error) {
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("v"))
	return
}

func (my *AVR_DAQ_MCU) GetNRegActual() (nreg uint, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("n"))
	if err == nil {
		_, err = fmt.Sscanf(string(resp), "%d", &nreg)
	}
	return
}
