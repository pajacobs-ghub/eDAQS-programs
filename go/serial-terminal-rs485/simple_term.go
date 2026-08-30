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
	"bytes"
	"flag"
	"fmt"
	"go.bug.st/serial"
	"log"
	"os"
	"time"
)

func wrap(txt []byte, id byte) (msg []byte) {
	s := [][]byte{[]byte("/"), []byte{id,}, txt, []byte("!")}
	return bytes.Join(s, []byte(""))
}

func unwrap(msg []byte) (txt []byte, id byte, err error) {
	txt = bytes.TrimSpace(msg)
	id = byte('0')
	err = nil
	if len(txt) == 0 {
		err = fmt.Errorf("empty message, %v", msg)
		return
	}
	islash := bytes.IndexByte(txt, byte('/'))
	ihash := bytes.IndexByte(txt, byte('#'))
	if islash < 0 || ihash < 0 {
		err = fmt.Errorf("message missing delimiter: %v", msg)
		return
	}
	if ihash <= islash+2 {
		err = fmt.Errorf("message missing content: %v", msg)
		return
	}
	id = msg[islash+1]
	txt = msg[islash+2:ihash]
	return
}

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
		log.Fatal(err)
	}
	mode := &serial.Mode{
		BaudRate: *baud,
	}
	port, err := serial.Open(*portName, mode)
	if err != nil {
		log.Fatal(err)
	}
	err = port.SetReadTimeout(timeOut)
	if err != nil {
		log.Fatal(err)
	}
	// Keep a single byte for the node identity.
	id := []byte(*nodeId)[0]
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
	bufferedPort := bufio.NewReader(port)
	for kbdScanner.Scan() {
		btext := kbdScanner.Bytes()
		if len(btext) > 0 {
			if *wrapMessages {
				btext = wrap(btext, id)
			}
			fmt.Printf("Command: %v\n", string(btext))
			n, err := port.Write(btext)
			if err != nil {
				log.Fatal(err)
			}
			_, err = port.Write([]byte("\n"))
			if err != nil {
				log.Fatal(err)
			}
			if err = port.Drain(); err != nil {
				log.Fatal(err)
			}
			fmt.Printf("Sent %v bytes followed by newline\n", n)
			//
			responseBytes, err := bufferedPort.ReadBytes('\n')
			if err != nil {
				fmt.Printf("Error: %v\n", err)
			} else {
				if *wrapMessages {
					responseBytes, _, err = unwrap(responseBytes)
					if err != nil {
						log.Printf("could not unwrap message: %v\n", err)
					}
				}
				fmt.Printf("Response: %v\n", string(responseBytes))
			}
		}
	}
	fmt.Println("Done.")
}
