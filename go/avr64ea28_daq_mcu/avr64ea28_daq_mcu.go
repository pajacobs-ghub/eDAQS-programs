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

func (my *AVR_DAQ_MCU) SetRegistersToFactoryValues() (err error) {
	_, err = my.comms_mcu.Command_DAQ_MCU([]byte("F"))
	return
}

func (my *AVR_DAQ_MCU) GetRegValue(i RegIndex) (val int, err error) {
	cmd := fmt.Sprintf("r %d", i)
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte(cmd))
	if err == nil {
		_, err = fmt.Sscanf(string(resp), "%d", &val)
	}
	return
}

func (my *AVR_DAQ_MCU) GetRegValues(indices []RegIndex) (vals []int, err error) {
	for _, i := range indices {
		var val int
		val, err = my.GetRegValue(i)
		if err != nil {
			err = fmt.Errorf("error while getting reg[%d]: %w", i, err)
			return
		}
		vals = append(vals, val)
	}
	return
}

func (my *AVR_DAQ_MCU) SetRegValue(i RegIndex, val int) (val2 int, err error) {
	cmd := fmt.Sprintf("s %d %d", i, val)
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte(cmd))
	if err == nil {
		var i2 int
		_, err = fmt.Sscanf(string(resp), "reg[%d] %d", &i2, &val2)
		if err == nil {
			if RegIndex(i2) != i || val != val2 {
				err = fmt.Errorf("returned numbers not consistent: %d!=%d or %d!=%d", i, i2, val, val2)
			}
		}
	}
	return
}

func (my *AVR_DAQ_MCU) SetRegValues(pairs map[RegIndex]int) (err error) {
	for i, val := range pairs {
		_, err = my.SetRegValue(i, val)
		if err != nil {
			err = fmt.Errorf("error while setting reg[%d]: %w", err)
			return
		}
	}
	return
}
