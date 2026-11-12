// ex_3.go
// Peter J. 2026-11-12

package main

import (
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f26q71_comms_4"
	daq "example.com/edaqs/pico2_daq_4x_ads131m04"
	"time"
)

func ex_3_immediate_short_recording(comms_mcu *comms.COMMS_4_MCU, daq_mcu *daq.Pico2_DAQ_MCU, nodeId string) {
	fmt.Println("Begin Test 3 Immediate-mode Short Recording...")
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
	// Report sample set an immediate-mode recording.
	_ = daq_mcu.SetRegistersToFactoryValues()
	_ = daq_mcu.SetPGA(0, 2, daq.X2)
	_ = daq_mcu.SetPGA(3, 0, daq.X2)
	_ = daq_mcu.SetTriggerImmediate()
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
	sSelect := daq.SampleSelection{PreTrigger: 0, Total: 100}
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
