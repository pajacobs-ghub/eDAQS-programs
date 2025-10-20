// simple_term.go
// Simple communication with RS485 nodes via the serial port.
//
// Following the documentation at https://pkg.go.dev/go.bug.st/serial
//
// Peter J. 2025-03-09

package main

import (
	"bufio"
	"fmt"
	"go.bug.st/serial"
	"log"
	"os"
	"time"
)

func main() {
	fmt.Println("Begin simple RS485 terminal program...")
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
	// Should allow overwrite of these default values
	// using command-line arguments.
	portName := "/dev/ttyUSB0"
	baud := 115200
	timeOut, err := time.ParseDuration("200ms")
	if err != nil {
		log.Fatal(err)
	}
	mode := &serial.Mode{
		BaudRate: baud,
	}
	port, err := serial.Open(portName, mode)
	if err != nil {
		log.Fatal(err)
	}
	err = port.SetReadTimeout(timeOut)
	if err != nil {
		log.Fatal(err)
	}

	// The main loop gets a line of text from the console and
	// sends it to the RS485 bus via the PC's serial port.
	// Note that it blocks while waiting for the newline character.
	//
	// It then waits for the reply line of text on the RS485 bus and
	// reports that, again waiting until a newline character arrives.
	// Notes:
	//   A single line of text is expected as the response.
	//   A timeOut may occur before the newline character arrives.

	fmt.Println("Enter commands to send on the RS485 bus.")
	fmt.Println("Press Ctrl-C to interrupt and quit program.")
	kbdScanner := bufio.NewScanner(os.Stdin)
	bufferedPort := bufio.NewReader(port)
	for kbdScanner.Scan() {
		btext := kbdScanner.Bytes()
		if len(btext) > 0 {
			fmt.Printf("Command: %v\n", string(btext))
			n, err := port.Write(btext)
			if err != nil {
				log.Fatal(err)
			}
			_, err = port.Write([]byte("\n"))
			if err != nil {
				log.Fatal(err)
			}
			fmt.Printf("Sent %v bytes followed by newline\n", n)
			responseBytes, err := bufferedPort.ReadBytes('\n')
			if err != nil {
				fmt.Printf("Error: %v\n", err)
			} else {
				fmt.Printf("Response: %v\n", string(responseBytes))
			}
		}
	}
	fmt.Println("Done.")
}
