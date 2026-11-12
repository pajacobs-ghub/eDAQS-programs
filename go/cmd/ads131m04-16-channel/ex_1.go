// ex_1.go
// Basic interactions with the PIC18F26Q71 COMMS-4 MCU and the Pico2 DAQ-MCU.
//
// Peter J. 2026-09-22 Built up from the simple-terminal program.

package main

import (
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f26q71_comms_4"
	daq "example.com/edaqs/pico2_daq_4x_ads131m04"
	"time"
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
    fmt.Println("Briefly turn on LED attached to RA7.")
    // bits                                      decimal
    //    7    6    5    4    3    2    1    0    value
    //    X    X    X    X  RA7  RA6  RA5  RA4
    //    0    0    0    0    0    1    1    1  ==  7
    //    0    0    0    0    1    0    0    0  ==  8
    _ = comms_mcu.UtilityPinsWriteANSEL(7) // RA7 as digital; others analog
    _ = comms_mcu.UtilityPinsWriteTRIS(7) // RA7 as output; others input
    _ = comms_mcu.UtilityPinsWriteLAT(8) // set RA7 high to turn LED on
	time.Sleep(2 * time.Second)
    _ = comms_mcu.UtilityPinsWriteLAT(0) // turn LED off
	//
	// Attempt to read the current room temperature from an attached TC74A0
	myBytes, err := comms_mcu.I2CRead(72, 1)
	if err != nil {
		log.Printf("I2C read error: %v\n", err)
	}
	if myBytes != nil {
		fmt.Printf("I2C bytes read: %v (should be room temperature in degrees C)\n", myBytes)
	}
	myBytes, _ = comms_mcu.I2CWrite(72, []byte{1,})
	if myBytes != nil {
		fmt.Printf("I2C bytes written: %v (next reading from status register)\n", myBytes)
	}
	myBytes, _ = comms_mcu.I2CRead(72, 1)
	if myBytes != nil {
		fmt.Printf("I2C bytes read: %v (should be 64 as content of status register)\n", myBytes)
	}
	myBytes, _ = comms_mcu.I2CWrite(72, []byte{0,})
	if myBytes != nil {
		fmt.Printf("I2C bytes written: %v (next reading from temperature register)\n", myBytes)
	}
	myBytes, _ = comms_mcu.I2CRead(72, 1)
	if myBytes != nil {
		fmt.Printf("I2C bytes read: %v (should again be room temperature in degrees C)\n", myBytes)
	}
	//
	// Exchange some bytes via SPI.
	// There does not need to be a device attached.
	// We can just use a logic analyser to check.
	_ = comms_mcu.SPIInit(3, 1, 0, 0)
	myBytes, _ = comms_mcu.SPIExchange([]byte{0, 1, 2, 3,})
	if myBytes != nil {
		fmt.Printf("SPI incoming bytes: %v (255 if no device is attached)\n", myBytes)
	}
	_ = comms_mcu.SPIClose()
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
