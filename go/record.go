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
// This description of the sampled-data record should work for
// the full range of eDAQS boards.
type Record struct {
	Data [][]int
	NChannels int
	NSamplesInRecord int
	NSamplesPreTrigger int
	DTmicroseconds float64
	LateFlag bool
	// The following slices will hold one value per channel.
	FullScaleVoltage []float64
	FullScaleCount []int
}

func (r *Record) AllocateDataSpace(nChannels int, nSamples int) {
	r.Data = make([][]int, nChannels)
	for ach := 0; ach < nChannels; ach++ {
		r.Data[ach] = make([]int, nSamples)
	}
	return
}

// Write the samples data in CSV format.
func (r Record) WriteData(w *bufio.Writer) {
	nchannels := len(r.Data)
	nsamples := len(r.Data[0])
	for i := 0; i < nsamples; i++ {
		var delim string
		for ch := 0; ch < nchannels; ch++ {
			if ch == 0 {
				delim = ""
			} else {
				delim = ","
			}
			w.WriteString(fmt.Sprintf("%s%d", delim, r.Data[ch][i]))
		}
		w.WriteString("\n")
	}
	w.Flush()
	return
}
