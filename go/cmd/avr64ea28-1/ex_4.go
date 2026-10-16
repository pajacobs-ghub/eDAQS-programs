// ex_4.go
// Peter J. 2026-10-16 make as a variation of ex_3

package main

import (
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f16q41_comms_1"
	daq "example.com/edaqs/avr64ea28_daq_mcu"
	"time"
)

func ex_4_transient_event_recording(comms_mcu *comms.COMMS_1_MCU, daq_mcu *daq.AVR_DAQ_MCU, nodeId string) {
	fmt.Println("Begin Test 4 Transient-Event Recording...")
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
	_ = comms_mcu.ReleaseEventLine()
	_ = comms_mcu.Reset_DAQ_MCU()
	time.Sleep(1 * time.Second)
	_ = daq_mcu.SetRegistersToFactoryValues()
	//
	// Set up two differential channels.
	_ = daq_mcu.SetNChannels(2)
	_ = daq_mcu.SetDifferentialConversion()
	chans := map[daq.RegIndex]daq.InputPin{
		daq.CH0P: daq.AIN28,
		daq.CH0N: daq.AIN29,
		daq.CH1P: daq.AIN30,
		daq.CH1N: daq.AIN31,
	}
	_ = daq_mcu.SetAnalogChannelPins(chans)
	chRegs := []daq.RegIndex{daq.CH0P, daq.CH0N, daq.CH1P, daq.CH1N, daq.CH2P, daq.CH2N}
	chPins, _ := daq_mcu.GetRegValues(chRegs)
	fmt.Printf("after setting some channels, register values: %v %v\n", chRegs, chPins)
	//
	_ = daq_mcu.SetPGA(daq.X4)
	_ = daq_mcu.SetAnalogRefVoltage(daq.Vref1024)
	//
	// Report sample set an immediate-mode recording.
	_ = daq_mcu.SetSamplePeriod_us(1000)
	_ = daq_mcu.SetTriggerInternal(0, 50, daq.SLOPE_POS)
	_ = daq_mcu.SetNSamples(100)
	//
	fmt.Println("Start sampling and wait until event has occurred and DAQ_MCU is not busy.")
	err = daq_mcu.StartSampling()
	if err != nil {
		log.Printf("oops, error while starting to sample: %v\n", err)
		return
	}
	for {
		fmt.Println("Waiting...")
		time.Sleep(1 * time.Second)
		done, _ := comms_mcu.Check_EventHasPassed()
		if done {
			break
		}
	}
	fmt.Println("Event has passed.")
	for {
		ready, _ := comms_mcu.Check_DAQ_MCU_Ready()
		if ready {
			break
		}
		time.Sleep(1 * time.Second)
	}
	fmt.Println("DAQ_MCU is ready.")
	sSelect := daq.SampleSelection{PreTrigger: 50, Total: 150}
	rec, err := daq_mcu.GetRecordedDataByIndex(&sSelect)
	if err != nil {
		log.Printf("oops: %v\n", err)
	}
	fmt.Printf("rec = %v\n", rec)
	//
	t := time.Now()
	fileName := fmt.Sprintf("%d-%02d-%02dT%02d-%02d-%02d-node-%s",
		t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), nodeId)
	err = rec.Save(fileName)
	if err != nil {
		log.Printf("oops: %v\n", err)
	}
	return
}
