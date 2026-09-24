// scan.go
// Scan the RS485 bus for nodes that respond.
//
// Peter J. 2026-09-25 Adapted from the simple terminal program.

package main

import (
	"flag"
	"fmt"
	"go.bug.st/serial"
	"log"
	edaqs "example.com/edaqs"
	"time"
)

func main() {
	fmt.Println("Begin scanning the RS485 bus...")
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
	timeStr := flag.String("timeout", "10ms", "Timeout, with units")
	flag.Parse()
	fmt.Printf("Selected serial port: %v\n", *portName)
	fmt.Printf("Baud rate: %v\n", *baud)
	fmt.Printf("When awaiting response, timeout: %v\n", *timeStr)
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
	ids := []byte("01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
	for _, id := range ids {
		fmt.Printf("%c", id)
		node := edaqs.NewRS485Node(&port, id)
		_, err = node.SendMessage([]byte("v"))
		if err != nil {
			log.Printf("error sending message for node %c: %v\n", id, err)
		}
		var response1 []byte
		response1, _, err = node.FetchResponse()
		if err == nil {
			_, _ = node.SendMessage([]byte("Xv"))
			response2, _, _ := node.FetchResponse()
			fmt.Printf("\nNode %c: %s %s\n", id, string(response1), string(response2))
		}
	}
	fmt.Println("\nDone.")
}
