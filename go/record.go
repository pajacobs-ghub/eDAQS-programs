// file: record.go
// The Record that contains the sampled, multichannel analog data for an event.
//
// Peter J.
// 2026-10-12: Abstracted from the AVR64EA28 code, Exercise 3.

package edaqs

import (
	"bufio"
	"fmt"
)

// Contains the sampled values as a slice of channel-records,
// each channel-record being a slice of int values representing
// the history of voltage on a particular analog channel.
type Record [][]int

type RecordMetaData struct {
	NChannels int
	NSamplesInRecord int
	NSamplesPreTrigger int
}

func NewRecord(meta RecordMetaData) (data Record) {
	nChannels := meta.NChannels
	nSamples := meta.NSamplesInRecord
	data = make([][]int, nChannels)
	for ach := 0; ach < nChannels; ach++ {
		data[ach] = make([]int, nSamples)
	}
	return
}

func (data Record) WriteCSV(w *bufio.Writer) {
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
