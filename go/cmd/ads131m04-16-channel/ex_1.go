// ex_1.go
// Peter J. 2026-09-22 Built up from the simple-terminal program.

package main

import (
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f26q71_comms_4"
	daq "example.com/edaqs/pico2_daq_4x_ads131m04"
	_ "time"
)

func ex_1_simple_interaction(comms_mcu *comms.COMMS_4_MCU, daq_mcu *daq.Pico2_DAQ_MCU) {
	fmt.Println("Begin Test 1 Simple Interaction...")
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
	// Light up the LED for 2 seconds
	// err = comms_mcu.SetLED(1)
	// time.Sleep(2 * time.Second)
	// err = comms_mcu.SetLED(0)
	//
	if eventFlag, err := comms_mcu.Check_EventHasPassed(); err == nil {
		if eventFlag {
			fmt.Println("Event has occurred.")
		} else {
			fmt.Println("Event has not occurred.")
		}
	} else {
		log.Println("Failed to read Event flag.")
	}
	if daqReadyFlag, err := comms_mcu.Check_DAQ_MCU_Ready(); err == nil {
		if daqReadyFlag {
			fmt.Println("DAQ MCU is ready.")
		} else {
			fmt.Println("DAQ MCU is busy.")
		}
	} else {
		log.Println("Failed to read DAQ_MCU Ready flag.")
	}
	//
	nreg, err := daq_mcu.GetNRegActual()
	if err != nil {
		log.Printf("error getting actual number of registers: %v\n", err)
	} else {
		fmt.Printf("number of registers in DAQ MCU: %d\n", nreg)
	}
	_ = daq_mcu.SetRegistersToFactoryValues()
	val, _ := daq_mcu.GetRegValue(daq.OSR_SELECT)
	fmt.Printf("before setting, OSR select: %d\n", val)
	err = daq_mcu.SetRegValue(daq.OSR_SELECT, int(daq.OSR_2048))
	if err != nil {
		log.Printf("error while setting register: %v\n", err)
	}
	regs := []daq.RegIndex{daq.OSR_SELECT, daq.NCHANNELS}
	vals, _ := daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting, register values: %v %v\n", regs, vals)
	pairs := map[daq.RegIndex]int{
		daq.OSR_SELECT: int(daq.OSR_256),
		daq.NCHANNELS: 4,
	}
	fmt.Println("Try setting via map")
	err = daq_mcu.SetRegValues(pairs)
	if err != nil {
		log.Printf("%v", err)
	}
	vals, _ = daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting via map, register values: %v %v\n", regs, vals)
	//
	err = daq_mcu.SetOSR(daq.OSR_2048)
	vals, _ = daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting OSR, register values: %v %v\n", regs, vals)
	//
	fCLKIN, err := daq_mcu.GetFreqCLKIN()
	if err != nil {
		log.Printf("%v", err)
	}
	fmt.Printf("fCLKIN= %d kHz\n", fCLKIN)
	//
	osr, err := daq_mcu.GetOSR()
	if err != nil {
		log.Printf("%v", err)
	}
	fmt.Printf("OSR= %d\n", osr)
	//
	str, _ := daq_mcu.GetAllRegValuesAsString()
	fmt.Printf("All register values= %s\n", str)
	return
}
