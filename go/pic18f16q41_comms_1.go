// file: pic18f16q41_comms_1.go
// Service functions for the communications MCU, which is a node on the RS485 bus.
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package edaqs

import (
	"bufio"
	"bytes"
	"fmt"
	"go.bug.st/serial"
	"log"
)

type COMMS_1_MCU struct {
	RS485Node
}

func NewCOMMS_1_MCU(sp *serial.Port, id byte) *COMMS_1_MCU {
	return &COMMS_1_MCU{
		port: sp,
		id: id,
		bufferedReader: bufio.NewReader(*sp),
	}
}

// Sends the text of a command to the COMMS MCU.
// Returns the text of the RS485 return message.
//
// Each command to the COMMS MCU is encoded as the first character
// of the command text. Any required data follows that character.
//
// The return message should start with the same command character
// and may have more text following that character.
// A command that is not successful should send back a message
// with the word "error" in it, together with some more information.
func (node *COMMS_1_MCU) command_COMMS_MCU(btext []byte) (resp []byte, err error) {
	cmdByte := btext[0]
	_, err = node.SendMessage(btext)
	if err != nil {
		log.Printf("error sending message: %v\n", err)
		return
	}
	resp, _, err = node.FetchResponse()
	if err != nil {
		log.Printf("error fetching response: %v\n", err)
		return
	}
	if bytes.Contains(resp, []byte("error")) {
		err = fmt.Errorf("response contains error message: %v", string(resp))
		return
	}
	resp = bytes.Trim(resp, " ")
	if resp[0] != cmdByte {
		err = fmt.Errorf("response string did not start with command byte: %v", string(resp))
		return
	}
	resp = bytes.Trim(resp[1:], " ")
	return
}

func (node *COMMS_1_MCU) GetVersion() (resp []byte, err error) {
	resp, err = node.command_COMMS_MCU([]byte("v"))
	return
}

// All interaction with the DAQ-MCU is via messages to the COMMS-MCU.
//
// Wraps the cmd_txt as a pass-through-command and sends it.
// Returns the unwrapped response text, if the response is ok.
func (node *COMMS_1_MCU) command_DAQ_MCU(btext []byte) (resp []byte, err error) {
	wholeCmd := bytes.Join([][]byte{[]byte("X"), btext}, []byte(""))
	resp, err = node.command_COMMS_MCU(wholeCmd)
	if err != nil {
		return
	}
	// Extract the good part of the DAQ_MCU response.
	resp = bytes.Trim(resp, " ")
	var found_ok bool
	resp, found_ok = bytes.CutSuffix(resp, []byte("ok"))
	if found_ok == false {
		err = fmt.Errorf("DAC_MCU response not ok: %s", resp)
	}
	return
}
