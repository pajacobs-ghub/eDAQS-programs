// file: pic18f26q71_comms_4.go
// Service functions for the communications MCU, which is a node on the RS485 bus.
//
// Peter J.
// 2026-09-22: Adapted from pic18f16q41_comms_1.go and the original Pythin functions.
//

package pic18f26q71_comms_4

import (
	"bufio"
	"bytes"
	"fmt"
	"go.bug.st/serial"
	"log"
	edaqs "example.com/edaqs"
)

type COMMS_4_MCU struct {
	edaqs.RS485Node
}

func NewCOMMS_4_MCU(sp *serial.Port, id byte) *COMMS_4_MCU {
	return &COMMS_4_MCU{
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
func (node *COMMS_4_MCU) Command_COMMS_MCU(btext []byte) (resp []byte, err error) {
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

func (node *COMMS_4_MCU) GetVersion() (resp []byte, err error) {
	resp, err = node.Command_COMMS_MCU([]byte("v"))
	return
}

// All interaction with the DAQ-MCU is via messages to the COMMS-MCU.
//
// Wraps the cmd_txt as a pass-through-command and sends it.
// Returns the unwrapped response text, if the response is ok.
func (node *COMMS_4_MCU) Command_DAQ_MCU(btext []byte) (resp []byte, err error) {
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

func (node *COMMS_4_MCU) UtilityPinsReadPORT() (b int, err error) {
	var resp []byte
	resp, err = node.Command_COMMS_MCU([]byte("u P"))
	if err != nil {
		return
	}
	_, err = fmt.Sscanf(string(resp), "%d", &b)
	return
}

func (node *COMMS_4_MCU) UtilityPinsWriteANSEL(val int) (err error) {
	wholeCmd := fmt.Sprintf("u A %d", val);
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

func (node *COMMS_4_MCU) UtilityPinsWriteTRIS(val int) (err error) {
	wholeCmd := fmt.Sprintf("u T %d", val);
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

func (node *COMMS_4_MCU) UtilityPinsWriteLAT(val int) (err error) {
	wholeCmd := fmt.Sprintf("u L %d", val);
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

func (node *COMMS_4_MCU) UtilityPinsWriteODC(val int) (err error) {
	wholeCmd := fmt.Sprintf("u O %d", val);
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

func (node *COMMS_4_MCU) UtilityPinsWriteWPU(val int) (err error) {
	wholeCmd := fmt.Sprintf("u W %d", val);
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

// TODO 2026-11-09 PJ Implement the UtilityPins functions
//   I2CWrite
//   I2CRead
//   SPIInit
//   SPIClose
//   SPIExchange

func (node *COMMS_4_MCU) AssertEventLineLow() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("t"))
	return
}

func (node *COMMS_4_MCU) ReleaseEventLine() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("z"))
	return
}

func (node *COMMS_4_MCU) Reset_DAQ_MCU() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("R"))
	return
}

func (node *COMMS_4_MCU) FlushRX2Buffer() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("F"))
	return
}

func (node *COMMS_4_MCU) Check_DAQ_MCU_Ready() (ready bool, err error) {
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

func (node *COMMS_4_MCU) Check_EventHasPassed() (passed bool, err error) {
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

// Use the PIC's ADC to sense voltage levels.
// Input:
// analog channel selector:
//   0=ANA0 (external trigger signal)
//   1=ANA1 (V_REF_A)
//   9=ANB1 (V_REF_B)
// Returns:
//   millivolts as an integer
//
// We have a 4096mV reference and we are using a 12-bit converter,
// so the integer count is already in millivolts.
func (node *COMMS_4_MCU) AnalogRead(pin int) (mV int, err error) {
	var resp []byte
	wholeCmd := fmt.Sprintf("a %d", pin);
	resp, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	if err != nil {
		return
	}
	_, err = fmt.Sscanf(string(resp), "%d", &mV)
	return
}

// Enable the analog-voltage output of the PIC MCU.
// levelA, levelB are 8-bit integers in range 0-255.
// The output is set at (level/256 * 4.096) Volts.
func (node *COMMS_4_MCU) Set_VREF_AB(levelA, levelB int) (err error) {
	if levelA < 0 {
		levelA = 0
	}
	if levelA > 255 {
		levelA = 255
	}
	if levelB < 0 {
		levelB = 0
	}
	if levelB > 255 {
		levelB = 255
	}
	wholeCmd := fmt.Sprintf("w %d %d", levelA, levelB)
	_, err = node.Command_COMMS_MCU([]byte(wholeCmd))
	return
}

func (node *COMMS_4_MCU) Get_VREF_AB_millivolts() (mVA int, mVB int, err error) {
	mVA, err = node.AnalogRead(1)
	if err != nil {
		return
	}
	mVA, err = node.AnalogRead(9)
	return
}

// Enable the external-trigger input to the PIC MCU.
//
// level is an 10-bit integer 0-1023.
// The analog trigger is set at (level/1024 * 4.096) Volts.
//
// With positive slope the EVENTn line is driven active-low
// when the external voltage exceeds the trigger level.
// With negative slope the EVENTn line is driven active-low
// when the external voltage becomes less than the trigger level.
//
// The comparator and latch will not be successfully enabled
// if the external-voltage condition already exceeds the level.
func (node *COMMS_4_MCU) EnableExternalTrigger(level int, slope int) (err error) {
	if level < 0 {
		level = 0
	}
	if level > 1023 {
		level = 1023
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

func (node *COMMS_4_MCU) DisableExternalTrigger() (err error) {
	_, err = node.Command_COMMS_MCU([]byte("d"))
	return
}

