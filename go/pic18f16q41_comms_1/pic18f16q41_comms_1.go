// file: pic18f16q41_comms_1.go
// Service functions for the communications MCU, which is a node on the RS485 bus.
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package pic18f16q41_comms_1

import (
	"bufio"
	"bytes"
	"fmt"
	"go.bug.st/serial"
	"log"
	edaqs "example.com/edaqs"
)

type COMMS_1_MCU struct {
	edaqs.RS485Node
}

func NewCOMMS_1_MCU(sp *serial.Port, id byte) *COMMS_1_MCU {
	return &COMMS_1_MCU{
		Port: sp,
		Id: id,
		BufferedReader: bufio.NewReader(*sp),
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
func (node *COMMS_1_MCU) Command_COMMS_MCU(btext []byte) (resp []byte, err error) {
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
	resp, err = node.Command_COMMS_MCU([]byte("v"))
	return
}

// All interaction with the DAQ-MCU is via messages to the COMMS-MCU.
//
// Wraps the cmd_txt as a pass-through-command and sends it.
// Returns the unwrapped response text, if the response is ok.
func (node *COMMS_1_MCU) Command_DAQ_MCU(btext []byte) (resp []byte, err error) {
	wholeCmd := bytes.Join([][]byte{[]byte("X"), btext}, []byte(""))
	resp, err = node.Command_COMMS_MCU(wholeCmd)
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

func (node *COMMS_1_MCU) SetLED(val uint) (err error) {
	wholeCmd := fmt.Sprintf("L%d", val)
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

func (node *COMMS_1_MCU) AssertEventLineLow() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("t"))
	return
}

func (node *COMMS_1_MCU) ReleaseEventLine() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("z"))
	return
}

func (node *COMMS_1_MCU) Reset_DAQ_MCU() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("R"))
	return
}

func (node *COMMS_1_MCU) FlushRX2Buffer() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("F"))
	return
}

func (node *COMMS_1_MCU) Check_DAQ_MCU_Ready() (ready bool, err error) {
	var resp []byte
	resp, err = node.Command_COMMS_MCU([]byte("Q"))
	if err != nil {
		return
	}
	var ievent, iready int
	_, err = fmt.Sscanf(string(resp), "%d %d", &ievent, &iready)
	ready = iready == 1
	_ = ievent
	return
}

func (node *COMMS_1_MCU) Check_EventHasPassed() (passed bool, err error) {
	var resp []byte
	resp, err = node.Command_COMMS_MCU([]byte("Q"))
	if err != nil {
		return
	}
	var ievent, iready int
	_, err = fmt.Sscanf(string(resp), "%d %d", &ievent, &iready)
	passed = ievent == 0
	_ = iready
	return
}

// Enable the analog-voltage output of the PIC MCU.
// level is an 8-bit integer 0-255.
// The output is set at (level/256 * 4.096) Volts.
func (node *COMMS_1_MCU) Set_VREF_ON(level int) (err error) {
	if level < 0 {
		level = 0
	}
	if level > 255 {
		level = 255
	}
	wholeCmd := fmt.Sprintf("w %d 1", level)
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

// Disable the analog-voltage output of the PIC MCU.
func (node *COMMS_1_MCU) Set_VREF_OFF() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("w 0 0"))
	return
}

// Enable the external-trigger input to the PIC MCU.
//
// level is an 8-bit integer 0-255.
// The analog trigger is set at (level/256 * 4.096) Volts.
//
// With positive slope the EVENT# line is driven active-low
// when the external voltage exceeds the trigger level.
// With negative slope the EVENT# line is driven active-low
// when the external voltage becomes less than the trigger level.
//
// The comparator and latch will not be successfully enabled
// if the external-voltage condition already exceeds the level.
func (node *COMMS_1_MCU) EnableExternalTrigger(level int, slope int) (err error) {
	if level < 0 {
		level = 0
	}
	if level > 255 {
		level = 255
	}
	if slope != 0 && slope != 1 {
		fmt.Errorf("invalid slope; should be either 1(positive) or 0(negative)")
		return
	}
	wholeCmd := fmt.Sprintf("e %d %d", level)
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	if err != nil {
		err = fmt.Errorf("could not set external trigger: %w", err)
	}
	return
}

func (node *COMMS_1_MCU) DisableExternalTrigger() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("d"))
	return
}

