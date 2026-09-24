// avr_exercise.go
// Exercise the AVR64EA28 eDAQS V 1 board.
//
// Peter J. 2026-09-22 Adapted from the simple terminal program.

package main

import (
	"flag"
	"fmt"
	"go.bug.st/serial"
	"log"
	comms "example.com/edaqs/pic18f16q41_comms_1"
	daq "example.com/edaqs/avr64ea28_daq_mcu"
	"time"
)

func main() {
	fmt.Println("Exercise the AVR64EA28 eDAQS V1 board...")
	ports, err := serial.GetPortsList()
	if err != nil {
		log.Fatal(err)
	}
	if len(ports) == 0 {
		log.Fatal("No serial ports found!")
	}
	for _, port := range ports {
		fmt.Printf("Found port: %v\n", port)
	}
	// These default values may be overridden using command-line flags.
	portName := flag.String("port", "/dev/ttyUSB0", "Name of the serial port")
	baud := flag.Int("baud", 115200, "Baud rate (bits per second)")
	timeStr := flag.String("timeout", "40ms", "Timeout, with units")
	itest := flag.Int("test", 1, "Test number (look at the source to see what is available")
	nodeId := flag.String("id", "1", "Single character node identity")
	flag.Parse()
	fmt.Printf("Selected serial port: %v\n", *portName)
	fmt.Printf("Baud rate: %v\n", *baud)
	fmt.Printf("When awaiting response, timeout: %v\n", *timeStr)
	fmt.Printf("Node Id (single character): %v\n", *nodeId)
	fmt.Printf("Test number: %d\n", *itest)
	//
	timeOut, err := time.ParseDuration(*timeStr)
	if err != nil {
		log.Fatal("failed to parse timeout: ", err)
	}
	mode := &serial.Mode{
		BaudRate: *baud,
	}
	port, err := serial.Open(*portName, mode)
	if err != nil {
		log.Fatal("failed to open serial port: ", err)
	}
	err = port.SetReadTimeout(timeOut)
	if err != nil {
		log.Fatal("failed to set timeout: ", err)
	}
	// Keep a single byte for the node identity.
	id := []byte(*nodeId)[0]
	comms_mcu := comms.NewCOMMS_1_MCU(&port, id)
	daq_mcu := daq.NewAVR_DAQ_MCU(comms_mcu)
	//
	switch *itest {
	case 1:
		ex_1_simple_interaction(comms_mcu, daq_mcu)
	default:
		fmt.Println("No test selected.")
	}
	fmt.Println("Done.")
}

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
	nreg, err := daq_mcu.GetNRegActual()
	if err != nil {
		log.Printf("error getting actual number of registers: %v\n", err)
	} else {
		fmt.Printf("number of registers in AVR: %d\n", nreg)
	}
	_ = daq_mcu.SetRegistersToFactoryValues()
	val, _ := daq_mcu.GetRegValue(daq.PER_TICKS)
	fmt.Printf("before setting, period_ticks: %d\n", val)
	_, err = daq_mcu.SetRegValue(daq.PER_TICKS, 99)
	if err != nil {
		log.Printf("error while setting register: %v\n", err)
	}
	regs := []daq.RegIndex{daq.PER_TICKS, daq.NCHANNELS}
	vals, _ := daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting, register values: %v %v\n", regs, vals)
	pairs := map[daq.RegIndex]int{daq.PER_TICKS: 88, daq.NCHANNELS: 4}
	fmt.Println("Try setting via map")
	err = daq_mcu.SetRegValues(pairs)
	if err != nil {
		log.Printf("%v", err)
	}
	vals, _ = daq_mcu.GetRegValues(regs)
	fmt.Printf("after setting via map, register values: %v %v\n", regs, vals)
	return
}
