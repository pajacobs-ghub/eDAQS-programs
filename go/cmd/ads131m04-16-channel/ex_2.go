// ex_2.go
// Peter J. 2026-10-01

package main

import (
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f26q71_comms_4"
	daq "example.com/edaqs/pico2_daq_4x_ads131m04"
)

func ex_2_immediate_sample_set(comms_mcu *comms.COMMS_4_MCU, daq_mcu *daq.Pico2_DAQ_MCU) {
	fmt.Println("Begin Test 2 Immediate Sample...")
	responseBytes, err := comms_mcu.GetVersion()
	if err != nil {
		log.Printf("error getting version from COMMS_MCU: %v\n", err)
	} else {
		fmt.Printf("COMMS_MCU version string: %v\n", string(responseBytes))
	}
	response2Bytes, err := daq_mcu.GetVersion()
	if err != nil {
		log.Printf("error getting version from DAQ_MCU: %v\n", err)
	} else {
		fmt.Printf("DAQ_MCU version string: %v\n", string(response2Bytes))
	}
	//
	// Report sample set for default register settings.
	_ = daq_mcu.SetRegistersToFactoryValues()
	data, err := daq_mcu.ImmediateSampleSet()
	if err != nil {
		log.Printf("oops: %v\n", err)
	}
	fmt.Printf("Returned data: %v\n", data)
	return
}
