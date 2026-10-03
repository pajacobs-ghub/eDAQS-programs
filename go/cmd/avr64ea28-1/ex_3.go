// ex_3.go
// Peter J. 2026-10-02

package main

import (
	"bufio"
	"fmt"
	"log"
	comms "example.com/edaqs/pic18f16q41_comms_1"
	daq "example.com/edaqs/avr64ea28_daq_mcu"
	"os"
	"path/filepath"
	"time"
)

func ex_3_immediate_short_recording(comms_mcu *comms.COMMS_1_MCU, daq_mcu *daq.AVR_DAQ_MCU) {
	fmt.Println("Begin Test 3 Immediate Short Recording...")
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
	_ = daq_mcu.SetTriggerImmediate()
	_ = daq_mcu.SetNSamples(10)
	fmt.Println("Start sampling and wait until event has occurred and DAQ_MCU is not busy.")
	err = daq_mcu.StartSampling()
	if err != nil {
		log.Printf("oops, error while starting to sample: %v\n", err)
		return
	}
	for {
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
	data, err := daq_mcu.GetRecordedData()
	if err != nil {
		log.Printf("oops: %v\n", err)
	}
	for ch := 0; ch < len(data); ch++ {
		fmt.Printf("channel %d: %v\n", ch, data[ch])
	}
	//
	// Open a file and write the data in CSV format.
	//
	t := time.Now()
	cwd, _ := os.Getwd()
	fileName := fmt.Sprintf("%d-%02d-%02dT%02d-%02d-%02d.data",
		t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second())
	path := filepath.Join(cwd, fileName)
	f, err := os.Create(path)
	if err != nil {
		log.Printf("failed to create file %v", path)
		return
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	nchannels := len(data)
	nsamples := len(data[0])
	for i := 0; i < nsamples; i++ {
		var delim string
		for ch := 0; ch < nchannels; ch++ {
			if ch == 0 {
				delim = ""
			} else {
				delim = ","
			}
			w.WriteString(fmt.Sprintf("%s%d", delim, data[ch][i]))
		}
		w.WriteString("\n")
	}
	w.Flush()
	return
}
