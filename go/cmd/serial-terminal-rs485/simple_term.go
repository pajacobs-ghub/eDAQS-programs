// simple_term.go
// Simple communication with RS485 nodes via the serial port.
//
// Following the documentation at https://pkg.go.dev/go.bug.st/serial
//
// Peter J. 2025-03-09
//          2026-08-30 Command-line flags, (un)wrapping of messages

package main

import (
	"bufio"
	"flag"
	"fmt"
	"go.bug.st/serial"
	"log"
	"os"
	edaqs "example.com/edaqs"
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
	// These default values may be overridden using command-line flags.
	portName := flag.String("port", "/dev/ttyUSB0", "Name of the serial port")
	baud := flag.Int("baud", 115200, "Baud rate (bits per second)")
	timeStr := flag.String("timeout", "40ms", "Timeout, with units")
	wrapMessages := flag.Bool("wrap", false, "Wrap commands and unwrap responses")
	nodeId := flag.String("id", "1", "Single character node identity")
	flag.Parse()
	fmt.Printf("Selected serial port: %v\n", *portName)
	fmt.Printf("Baud rate: %v\n", *baud)
	fmt.Printf("When awaiting response, timeout: %v\n", *timeStr)
	fmt.Printf("Node Id (single character): %v\n", *nodeId)
	if *wrapMessages {
		fmt.Println("Wrap commands and unwrap responses")
	} else {
		fmt.Println("Raw commands and responses")
	}
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
	node := edaqs.NewRS485Node(&port, id)
	//
	// The main loop gets a line of text from the console and
	// sends it to the RS485 bus via the PC's serial port.
	// Note that it blocks while waiting for the newline character.
	//
	// It then waits for the reply line of text on the RS485 bus and
	// reports that, again waiting until a newline character arrives.
	// Notes:
	//   A single line of text is expected as the response.
	//   A timeOut may occur before the newline character arrives.
	//   It may be that the wrapping of the serial port with the
	//   buffered reader is not quite working as we expect.
	//   For a non-existing node, the error reported is
	//   "multiple Read calls return no data or error".
	//
	fmt.Println("Enter commands to send on the RS485 bus.")
	fmt.Println("Press Ctrl-C to interrupt and quit program.")
	kbdScanner := bufio.NewScanner(os.Stdin)
	for kbdScanner.Scan() {
		btext := kbdScanner.Bytes()
		if len(btext) > 0 {
			fmt.Printf("Command: %v\n", string(btext))
			var n int
			if *wrapMessages {
				n, err = node.SendMessage(btext)
			} else {
				n, err = node.SendRawMessage(btext)
			}
			if err != nil {
				log.Printf("error sending message: %v\n", err)
			}
			fmt.Printf("Sent %v bytes followed by newline\n", n)
			//
			var responseBytes []byte
			if *wrapMessages {
				responseBytes, _, err = node.FetchResponse()
			} else {
				responseBytes, err = node.FetchRawResponse()
			}
			fmt.Printf("Response: %v\n", string(responseBytes))
		}
	}
	fmt.Println("Done.")
}
