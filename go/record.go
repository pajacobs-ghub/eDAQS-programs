// file: record.go
// The Record that contains the sampled, multichannel analog data for an event.
//
// Peter J.
// 2026-10-12: Abstracted from the AVR64EA28 code, Exercise 3.

package edaqs

import (
	"bufio"
	"encoding/json/v2"
	"fmt"
	"log"
	"os"
	"path/filepath"
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

// Write the metadata in JSON format.
func (r Record) WriteMetaData(w *bufio.Writer) {
	w.WriteString(fmt.Sprintf("{\n"))
	nchannels := len(r.Data)
	if nchannels != r.NChannels {
		log.Printf("metadata does not match actual data arrays nchannels %d %d",
			nchannels, r.NChannels)
	}
	w.WriteString(fmt.Sprintf("%q : %d,\n", "nchannels", r.NChannels))
	nsamples := len(r.Data[0])
	if nsamples != r.NSamplesInRecord {
		log.Printf("metadata does not match actual data arrays nsamples %d %d",
			nsamples, r.NSamplesInRecord)
	}
	w.WriteString(fmt.Sprintf("%q : %d,\n", "nsamples", r.NSamplesInRecord))
	w.WriteString(fmt.Sprintf("%q : %d,\n", "npretrigger", r.NSamplesPreTrigger))
	w.WriteString(fmt.Sprintf("%q : %g,\n", "dt_us", r.DTmicroseconds))
	outBytes, _ := json.Marshal(r.LateFlag)
	w.WriteString(fmt.Sprintf("%q : %s,\n", "late_flag", string(outBytes)))
	outBytes, _ = json.Marshal(r.FullScaleVoltage)
	w.WriteString(fmt.Sprintf("%q : %s,\n", "fullscale_voltage", string(outBytes)))
	outBytes, _ = json.Marshal(r.FullScaleCount)
	w.WriteString(fmt.Sprintf("%q : %s,\n", "fullscale_count", string(outBytes)))
	w.WriteString(fmt.Sprintf("%q : %q\n}\n", "dummy", "entry"))
	w.Flush()
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

// Write the data to a CSV file in the current directory,
// and write to metadata to a JSON file.
func (r Record) Save(fileName string) (err error) {
	cwd, _ := os.Getwd()
	//
	// Write the metadata to a JSON file.
	path := filepath.Join(cwd, fileName + ".json")
	fj, err := os.Create(path)
	if err != nil {
		err = fmt.Errorf("failed to create JSON file %v: %w", path, err)
		return
	}
	defer fj.Close()
	wj := bufio.NewWriter(fj)
	r.WriteMetaData(wj)
	//
	// Write the sample data to the CSV file.
	path = filepath.Join(cwd, fileName + ".csv")
	fc, err := os.Create(path)
	if err != nil {
		err = fmt.Errorf("failed to create CSV file %v: %w", path, err)
		return
	}
	defer fc.Close()
	wc := bufio.NewWriter(fc)
	r.WriteData(wc)
	return
}

