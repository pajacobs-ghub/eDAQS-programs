// file: rs485.go
// Basic functions for sending and receiving messages across the RS485 bus.
//
// The RS485 communication happens through a standard serial port
// and we use the go.bug.st/serial package to manage that port.
//
// Each node on the RS485 bus should listen to all messages but
// accept and act only on the messages addressed to their id.
// The controlling node (master) has id character b'0'.
// Other nodes may be '1', '2', ... 'A' .. 'Z', 'a' .. 'z'.
//
// Command messages are of the form: /<id><message text>!\n
// where <id> is the single byte identity of the target node.
// Response messages are of the form: /0<message text>#\n
// where 0 is the byte identity of the master node (a personal computer, say).
// Details of the message text is specific to each model of node.
//
// For further notes, see PJ's workbook page 76, 2024-01-09.
//
// Peter J.
// 2026-09-22 functions extracted from the simple-terminal program.

package edaqs

import (
	"bufio"
	"bytes"
	"fmt"
	"go.bug.st/serial"
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

type RS485Node struct {
	Port *serial.Port
	Id byte
	BufferedReader *bufio.Reader
}

func NewRS485Node(sp *serial.Port, id byte) *RS485Node {
	return &RS485Node{
		Port: sp,
		Id: id,
		BufferedReader: bufio.NewReader(*sp),
	}
}

func (node *RS485Node) SendRawMessage(btext []byte) (n int, err error) {
	port := *node.Port
	n, err = port.Write(btext)
	if err != nil {
		err = fmt.Errorf("error trying to send raw message: %w", err)
		return
	}
	_, err = port.Write([]byte("\n"))
	if err != nil {
		err = fmt.Errorf("error sending newline char: %w", err)
		return
	}
	if err = port.Drain(); err != nil {
		err = fmt.Errorf("error draining serial port buffer: %w", err)
		return
	}
	return
}

func (node *RS485Node) SendMessage(btext []byte) (n int, err error) {
	btext = wrap(btext, node.Id)
	n, err = node.SendRawMessage(btext)
	return
}

func (node *RS485Node) FetchRawResponse() (btext []byte, err error) {
	btext, err = node.BufferedReader.ReadBytes('\n')
	if err != nil {
		err = fmt.Errorf("error fetching raw response: %w", err)
	}
	return
}

func (node *RS485Node) FetchResponse() (btext []byte, id byte, err error) {
	btext, err = node.FetchRawResponse()
	if err != nil {
		err = fmt.Errorf("error fetching response: %w", err)
		return
	}
	btext, id, err = unwrap(btext)
	if err != nil {
		err = fmt.Errorf("error unwrapping message: %w", err)
	}
	return
}

