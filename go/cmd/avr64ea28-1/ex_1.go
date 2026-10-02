// ex_1.go
// Peter J. 2026-09-22 Built up from the simple-terminal program.

package main

import (
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f16q41_comms_1"
	daq "example.com/edaqs/avr64ea28_daq_mcu"
	"time"
)

func ex_1_simple_interaction(comms_mcu *comms.COMMS_1_MCU, daq_mcu *daq.AVR_DAQ_MCU) {
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
	err = comms_mcu.SetLED(1)
	time.Sleep(2 * time.Second)
	err = comms_mcu.SetLED(0)
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
		fmt.Printf("number of registers in AVR: %d\n", nreg)
	}
	_ = daq_mcu.SetRegistersToFactoryValues()
	val, _ := daq_mcu.GetRegValue(daq.PER_TICKS)
	fmt.Printf("before setting, period_ticks: %d\n", val)
	err = daq_mcu.SetRegValue(daq.PER_TICKS, 99)
	if err != nil {
		log.Printf("error while setting register: %v\n", err)
	}
	regs := []daq.RegIndex{daq.PER_TICKS, daq.NCHANNELS}
	vals, _ := daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting, register values: %v %v\n", regs, vals)
	pairs := map[daq.RegIndex]int{
		daq.PER_TICKS: 88,
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
	err = daq_mcu.SetSamplePeriod_us(200)
	vals, _ = daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting sample period, register values: %v %v\n", regs, vals)
	//
	dt, err := daq_mcu.GetSamplePeriod_us()
	if err != nil {
		log.Printf("%v", err)
	}
	fmt.Printf("sample period= %g microseconds\n", dt)
	//
	chans := map[daq.RegIndex]daq.InputPin{
		daq.CH0P: daq.AIN31,
		daq.CH0N: daq.GND,
	}
	err = daq_mcu.SetAnalogChannels(chans)
	chRegs := []daq.RegIndex{daq.CH0P, daq.CH0N, daq.CH1P, daq.CH1N, daq.CH2P, daq.CH2N}
	chPins, _ := daq_mcu.GetRegValues(chRegs)
	fmt.Printf("after setting some channels, register values: %v %v\n", chRegs, chPins)
	//
	gainRegs := []daq.RegIndex{daq.PGA_FLAG, daq.PGA_GAIN}
	regValues, _ := daq_mcu.GetRegValues(gainRegs)
	fmt.Printf("before setting gain, register values: %v %v\n", gainRegs, regValues)
	gain, _ := daq_mcu.GetAnalogGain()
	fmt.Printf("analog gain: %v\n", gain)
	err = daq_mcu.SetPGA(daq.X16)
	regValues, _ = daq_mcu.GetRegValues(gainRegs)
	fmt.Printf("after setting gain, register values: %v %v\n", gainRegs, regValues)
	gain, _ = daq_mcu.GetAnalogGain()
	fmt.Printf("analog gain: %v\n", gain)
	err = daq_mcu.ClearPGA()
	regValues, _ = daq_mcu.GetRegValues(gainRegs)
	fmt.Printf("after clearing gain, register values: %v %v\n", gainRegs, regValues)
	gain, _ = daq_mcu.GetAnalogGain()
	fmt.Printf("analog gain: %v\n", gain)
	//
	vref, _ := daq_mcu.GetAnalogRefVoltage()
	fmt.Printf("default analog reference voltage: %v\n", vref)
	_ = daq_mcu.SetAnalogRefVoltage(daq.Vref2048)
	vref, _ = daq_mcu.GetAnalogRefVoltage()
	fmt.Printf("set analog reference voltage: %v\n", vref)
	//
	acc, _ := daq_mcu.GetBurst()
	fmt.Printf("default burst accumulation samples: %v\n", acc)
	_ = daq_mcu.SetBurst(daq.ACC256)
	acc, _ = daq_mcu.GetBurst()
	fmt.Printf("set burst accumulation samples: %v\n", acc)
	//
	str, _ := daq_mcu.GetAllRegValuesAsString()
	fmt.Printf("All register values= %s\n", str)
	return
}
