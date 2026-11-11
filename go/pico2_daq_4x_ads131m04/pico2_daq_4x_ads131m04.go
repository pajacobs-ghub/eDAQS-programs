// file: pico2_daq_4x_ads131m04.go
// Service functions for the Pico2 DAQ MCU driving 4x ADS131M04 analog converter chips..
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package pico2_daq_4x_ads131m04

import (
	_ "encoding/hex"
	"fmt"
	"strconv"
	"strings"
	comms "example.com/edaqs/pic18f26q71_comms_4"
	edaqs "example.com/edaqs"
)


type Pico2_DAQ_MCU struct {
	comms_mcu *comms.COMMS_4_MCU
}

func NewPico2_DAQ_MCU(comms_mcu *comms.COMMS_4_MCU) *Pico2_DAQ_MCU {
	return &Pico2_DAQ_MCU{
		comms_mcu: comms_mcu,
	}
}

// Low-level functions

func (my *Pico2_DAQ_MCU) GetVersion() (resp []byte, err error) {
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("v"))
	return
}

func (my *Pico2_DAQ_MCU) GetNRegActual() (nreg uint, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("n"))
	if err == nil {
		_, err = fmt.Sscanf(string(resp), "%d", &nreg)
	}
	return
}

func (my *Pico2_DAQ_MCU) SetRegistersToFactoryValues() (err error) {
	_, err = my.comms_mcu.Command_DAQ_MCU([]byte("F"))
	return
}

func (my *Pico2_DAQ_MCU) GetRegValue(i RegIndex) (val int, err error) {
	cmd := fmt.Sprintf("r %d", i)
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte(cmd))
	if err == nil {
		_, err = fmt.Sscanf(strings.TrimSpace(string(resp)), "%d", &val)
	}
	return
}

func (my *Pico2_DAQ_MCU) GetRegValues(indices []RegIndex) (vals []int, err error) {
	for _, i := range indices {
		var val int
		val, err = my.GetRegValue(i)
		if err != nil {
			err = fmt.Errorf("error while getting reg[%d]: %w", i, err)
			return
		}
		vals = append(vals, val)
	}
	return
}

func (my *Pico2_DAQ_MCU) GetAllRegValuesAsString() (vals string, err error) {
	var builder strings.Builder
	for i := 0; i < NReg; i++ {
		var val int
		val, err = my.GetRegValue(RegIndex(i))
		if err != nil {
			err = fmt.Errorf("error while getting reg[%d]: %w", i, err)
			return
		}
		if i > 0 {
			builder.WriteString(", ")
		}
		builder.WriteString(fmt.Sprintf("%v:%d", RegIndex(i), val))
	}
	vals = builder.String()
	return
}

func (my *Pico2_DAQ_MCU) SetRegValue(i RegIndex, val int) (err error) {
	cmd := fmt.Sprintf("s %d %d", i, val)
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte(cmd))
	if err == nil {
		var i2, val2 int
		_, err = fmt.Sscanf(string(resp), "reg[%d] %d", &i2, &val2)
		if err == nil {
			if RegIndex(i2) != i || val != val2 {
				err = fmt.Errorf("returned numbers not consistent: %d!=%d or %d!=%d", i, i2, val, val2)
			}
		}
	}
	return
}

func (my *Pico2_DAQ_MCU) SetRegValues(pairs map[RegIndex]int) (err error) {
	for i, val := range pairs {
		err = my.SetRegValue(i, val)
		if err != nil {
			err = fmt.Errorf("error while setting reg[%d]: %w", i, err)
			return
		}
	}
	return
}

func (my *Pico2_DAQ_MCU) SetFreqCLKIN(f_kHz int) (err error) {
	if f_kHz < 512 {
		f_kHz = 512
	}
	if f_kHz > 8192 {
		f_kHz = 8192
	}
	err = my.SetRegValue(MCLK_KHZ, f_kHz)
	return
}

func (my *Pico2_DAQ_MCU) GetFreqCLKIN() (f_kHz int, err error) {
	f_kHz, err = my.GetRegValue(MCLK_KHZ)
	if err != nil {
		err = fmt.Errorf("failed to read MCLK_KHZ register: %w", err)
		return
	}
	return
}

func (my *Pico2_DAQ_MCU) SetOSR(osr OSRSelect) (err error) {
	err = my.SetRegValue(OSR_SELECT, int(osr))
	return
}

func (my *Pico2_DAQ_MCU) GetOSR() (osr int, err error) {
	i, err := my.GetRegValue(OSR_SELECT)
	if err != nil {
		err = fmt.Errorf("failed to read OSR_SELECT register: %w", err)
		return
	}
	osr = OSRSelect(i).Int()
	return
}

func (my *Pico2_DAQ_MCU) SetPower(pwr PowerSelect) (err error) {
	err = my.SetRegValue(PWR_SELECT, int(pwr))
	return
}

func (my *Pico2_DAQ_MCU) GetPower() (pwr PowerSelect, err error) {
	i, err := my.GetRegValue(PWR_SELECT)
	if err != nil {
		err = fmt.Errorf("failed to read PWR_SELECT register: %w", err)
		return
	}
	pwr = PowerSelect(i)
	return
}

func (my *Pico2_DAQ_MCU) SetPGA(ichip int, ichan int, gain PGAGain) (err error) {
	ireg := int(GAIN_AIN0_0) + ichip*4 + ichan
	err = my.SetRegValue(RegIndex(ireg), int(gain))
	return
}

func (my *Pico2_DAQ_MCU) GetAnalogGain(ichip int, ichan int) (gain float64, err error) {
	ireg := int(GAIN_AIN0_0) + ichip*4 + ichan
	var i int
	i, err = my.GetRegValue(RegIndex(ireg))
	gain = PGAGain(i).Float()
	return
}

func (my *Pico2_DAQ_MCU) ImmediateSampleSet() (vals []int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("I"))
	if err != nil {
		err = fmt.Errorf("error getting immediate sample set: %w", err)
		return
	}
	items := strings.Fields(string(resp))
	n := len(items)
	vals = make([]int, n)
	for i := 0; i < n; i++ {
		vals[i], err = strconv.Atoi(items[i])
		if err != nil {
			err = fmt.Errorf("error while getting immediate sample set, converting %s to int: %w",
				items[i], err)
			return
		}
	}
	return
}

// Recording will start immediately that the MCU is told to start sampling
// and will stop after nsamples have been recorded.
func (my *Pico2_DAQ_MCU) SetTriggerImmediate() (err error) {
	err = my.SetRegValue(TRIG_MODE, int(IMMEDIATE))
	if err != nil {
		err = fmt.Errorf("error while trying to set immediate trigger: %w", err)
		return
	}
	return
}

// Recording will start immediately that the MCU is told to start sampling
// and will continue indefinitely, until the specified channel crosses
// the specified level.
// nsamples with then be recorded and the sampling stops.
func (my *Pico2_DAQ_MCU) SetTriggerInternal(channel int, level int, slope TriggerSlope) (err error) {
	err = my.SetRegValue(TRIG_MODE, int(INTERNAL))
	if err != nil {
		err = fmt.Errorf("error setting immediate trigger: %w", err)
		return
	}
	err = my.SetRegValue(TRIG_CHAN, channel)
	if err != nil {
		err = fmt.Errorf("error setting trigger channel: %w", err)
		return
	}
	err = my.SetRegValue(TRIG_LEVEL, level)
	if err != nil {
		err = fmt.Errorf("error setting trigger level: %w", err)
		return
	}
	err = my.SetRegValue(TRIG_SLOPE, int(slope))
	if err != nil {
		err = fmt.Errorf("error setting trigger slope: %w", err)
		return
	}
	return
}

// Recording will start immediately that the MCU is told to start sampling
// and will continue indefinitely, until the EVENT# pin goes low.
// nsamples with then be recorded and the sampling stops.
func (my *Pico2_DAQ_MCU) SetTriggerExternal() (err error) {
	err = my.SetRegValue(TRIG_MODE, int(EXTERNAL))
	return
}

func (my *Pico2_DAQ_MCU) GetTriggerMode() (m TriggerMode, err error) {
	var i int
	i, err = my.GetRegValue(TRIG_MODE)
	m = TriggerMode(i)
	return
}

// NSAMPLES is the number of samples to be recorded after trigger event.
func (my *Pico2_DAQ_MCU) SetNSamples(n int) (err error) {
	if n < 0 {
		// Somewhat arbitrary.
		n = 100
	}
	err = my.SetRegValue(NSAMPLES, n)
	return
}

func (my *Pico2_DAQ_MCU) GetNSamples() (n int, err error) {
	n, err = my.GetRegValue(NSAMPLES)
	return
}

func (my *Pico2_DAQ_MCU) SetNChannels(n int) (err error) {
	if n < 0 {
		// Somewhat arbitrary.
		n = 1
	}
	if n > 16 {
		n = 16
	}
	err = my.SetRegValue(NCHANNELS, n)
	return
}

func (my *Pico2_DAQ_MCU) GetNChannels() (n int, err error) {
	n, err = my.GetRegValue(NCHANNELS)
	return
}

// What happens after calling this function depends on the register settings
// and, maybe, the external signals.
func (my *Pico2_DAQ_MCU) StartSampling() (err error) {
	_, err = my.comms_mcu.Command_DAQ_MCU([]byte("g"))
	if err != nil {
		err = fmt.Errorf("error while trying to start sampling: %w", err)
		return
	}
	return
}

// Returns the values of the recorded sample set i,
// where i is counted from the oldest recorded sample (i=0).
//
// The AVR reports these values as a string of space-separated integers.
func (my *Pico2_DAQ_MCU) GetSampleSet(i int) (vals []int, err error) {
	cmd := fmt.Sprintf("P %d", i)
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte(cmd))
	if err != nil {
		err = fmt.Errorf("error getting sample set %d: %w", i, err)
		return
	}
	items := strings.Fields(string(resp))
	n := len(items)
	vals = make([]int, n)
	for i := 0; i < n; i++ {
		vals[i], err = strconv.Atoi(items[i])
		if err != nil {
			err = fmt.Errorf("error while getting sample set %d, converting %s to int: %w",
				i, items[i], err)
			return
		}
	}
	return
}

// Returns a code for the last error logged during sampling.
func (my *Pico2_DAQ_MCU) LastError() (didNotKeepUpDuringSampling int,
	sampleErrorCode int, exchangeErrorCode int, dmaUnfinishedMask uint,
	err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("k"))
	if err != nil {
		err = fmt.Errorf("error while getting last error codes: %w", err)
		return
	}
	_, err = fmt.Sscanf(string(resp), "%d %d %d %u", &didNotKeepUpDuringSampling,
		&sampleErrorCode, &exchangeErrorCode, &dmaUnfinishedMask)
	return
}

// Returns the number of bytes used to store one sample set in SRAM.
// Depends upon the number of channels being recorded.
func (my *Pico2_DAQ_MCU) GetByteSizeOfSampleSet() (n int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("b"))
	if err != nil {
		err = fmt.Errorf("error while getting byte-size of sample set: %w", err)
		return
	}
	n, err = strconv.Atoi(strings.TrimSpace(string(resp)))
	if err != nil {
		err = fmt.Errorf("error while getting byte-size of sample set: %w", err)
	}
	return
}

// Returns the number of sample sets that can be stored in SRAM.
//
// This value is dependent on the total amount of SRAM installed
// and the number of channels being recorded.
func (my *Pico2_DAQ_MCU) GetMaxNSamples() (n int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("m"))
	if err != nil {
		err = fmt.Errorf("error while getting max NSAMPLES: %w", err)
		return
	}
	n, err = strconv.Atoi(strings.TrimSpace(string(resp)))
	if err != nil {
		err = fmt.Errorf("error while getting max NSAMPLES: %w", err)
	}
	return
}

func (my *Pico2_DAQ_MCU) GetSizeOfSRAMInBytes() (n int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("T"))
	if err != nil {
		err = fmt.Errorf("error while getting size of SRAM: %w", err)
		return
	}
	n, err = strconv.Atoi(strings.TrimSpace(string(resp)))
	if err != nil {
		err = fmt.Errorf("error while getting size of SRAM: %w", err)
	}
	return
}

// Returns the byte-address.
//
// Since the SRAM memory is treated as a circular buffer,
// this address may be almost anywhere in the available range.
// The possible sizes of each sample set is restricted
// so that sample sets fit neatly into the available SRAM space.
// A sample set will not be split over the end/beginning of
// the address-space.
//
// Until one full pass of the data space, this address will sit at zero.
// Once the data space has been filled and the address wraps,
// this returned address will be the same as for the next data to be written.
func (my *Pico2_DAQ_MCU) GetByteAddressOfOldestData() (n int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("a"))
	if err != nil {
		err = fmt.Errorf("error while getting byte address of oldest data: %w", err)
		return
	}
	n, err = strconv.Atoi(strings.TrimSpace(string(resp)))
	if err != nil {
		err = fmt.Errorf("error while getting byte address of oldest data: %w", err)
	}
	return
}

// Returns the byte-address of the next data sample to be written
// into the SRAM memory.
//
// Since the SRAM memory is treated as a circular buffer,
// this address may be almost anywhere in the available range
// and will wrap around once the memory is full.
//
// The possible sizes of each sample set is restricted
// so that sample sets fit neatly into the available SRAM space.
// A sample set will not be split over the end/beginning of
// the address-space.
func (my *Pico2_DAQ_MCU) GetByteAddressOfNextData() (n int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("A"))
	if err != nil {
		err = fmt.Errorf("error while getting byte address of next data: %w", err)
		return
	}
	n, err = strconv.Atoi(strings.TrimSpace(string(resp)))
	if err != nil {
		err = fmt.Errorf("error while getting byte address of next data: %w", err)
	}
	return
}

// Returns the number of 32-byte pages in the SRAM storage.
func (my *Pico2_DAQ_MCU) GetSizeOfSRAMInPages() (n int, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("N"))
	if err != nil {
		err = fmt.Errorf("error while getting pages in SRAM: %w", err)
		return
	}
	n, err = strconv.Atoi(strings.TrimSpace(string(resp)))
	if err != nil {
		err = fmt.Errorf("error while getting pages in SRAM: %w", err)
	}
	return
}

// Higher-level functions

// The description of the sampled-data record held by the DAQ MCU
type RecordMetaData struct {
	NChannels int
	MaxNSamples int
	NSamplesInRecord int
	NSamplesAfterTrigger int
	NSamplesPreTrigger int
	TriggerSample int
	ByteAddrOldestData int
	ByteAddrNextData int
	TotalBytes int
	TotalPages int
	BytesPerSampleSet int
	Mode TriggerMode
	FreqCLKINkHz int
	OSR int
	DTmicroseconds float64
	LastErrorCode int
	LateFlag bool
	// The following slices will hold one value per channel.
	FullScaleVoltage []float64
	FullScaleCount []int
}

func (my *Pico2_DAQ_MCU) GetRecordMetaData() (m RecordMetaData, err error) {
	// Read the current information from the DAQ MCU
	// to construct the metadata for the recording that was made.
	m.NChannels, err = my.GetNChannels()
	if err != nil {
		err = fmt.Errorf("failed to get nChannels from DAQ_MCU: %w", err)
		return
	}
	//
	// Maximum number of samples that could be stored in the DAQ MCU's SRAM.
	m.MaxNSamples, err = my.GetMaxNSamples()
	if err != nil {
		err = fmt.Errorf("failed to get MAX nSamples from DAQ_MCU: %w", err)
		return
	}
	//
	m.NSamplesAfterTrigger, err = my.GetNSamples()
	if err != nil {
		err = fmt.Errorf("failed to get nSamples from DAQ_MCU: %w", err)
		return
	}
	//
	m.ByteAddrOldestData, err = my.GetByteAddressOfOldestData()
	if err != nil {
		err = fmt.Errorf("failed to get byte address of oldest data from DAQ_MCU: %w", err)
		return
	}
	m.ByteAddrNextData, err = my.GetByteAddressOfNextData()
	if err != nil {
		err = fmt.Errorf("failed to get byte address of NEXT data from DAQ_MCU: %w", err)
		return
	}
	m.TotalBytes, err = my.GetSizeOfSRAMInBytes()
	if err != nil {
		err = fmt.Errorf("failed to get size of SRAM in bytes from DAQ_MCU: %w", err)
		return
	}
	m.TotalPages, err = my.GetSizeOfSRAMInPages()
	if err != nil {
		err = fmt.Errorf("failed to get size of SRAM in pages from DAQ_MCU: %w", err)
		return
	}
	m.BytesPerSampleSet, err = my.GetByteSizeOfSampleSet()
	if err != nil {
		err = fmt.Errorf("failed to get size of sample-set in bytes from DAQ_MCU: %w", err)
		return
	}
	if m.ByteAddrOldestData == m.ByteAddrNextData {
		// Wrap-around has occurred while recording, so
		// the recorded data completely fills the SRAM storage.
		m.NSamplesInRecord = m.MaxNSamples
	} else {
		// Wrap-around in SRAM address space did not happen happen, so
		// we have fewer samples in the actual recording stored in SRAM.
		m.NSamplesInRecord = m.ByteAddrNextData / m.BytesPerSampleSet
	}
	//
	m.Mode, err = my.GetTriggerMode()
	if err != nil {
		err = fmt.Errorf("failed to get trigger mode from DAQ_MCU: %w", err)
		return
	}
	if m.Mode == IMMEDIATE {
		m.TriggerSample = 0
		m.NSamplesPreTrigger = 0
	} else {
		m.TriggerSample = m.NSamplesInRecord - m.NSamplesAfterTrigger
		m.NSamplesPreTrigger = m.NSamplesInRecord - m.NSamplesAfterTrigger
	}
	//
	m.FreqCLKINkHz, err = my.GetFreqCLKIN()
	if err != nil {
		err = fmt.Errorf("failed to get frequency of CLKIN from DAQ_MCU: %w", err)
		return
	}
	m.OSR, err = my.GetOSR()
	if err != nil {
		err = fmt.Errorf("failed to get frequency of OSR from DAQ_MCU: %w", err)
		return
	}
	// Modulator runs at half the input frequency.
	dtMod := 1000.0 / float64(m.FreqCLKINkHz) * 2.0
	// Data sample period is then set by the over-sampling ratio.
	m.DTmicroseconds = dtMod * float64(m.OSR)
	//
	var iLate int
	iLate, m.LastErrorCode, _, _, err = my.LastError()
	if err != nil {
		err = fmt.Errorf("failed to get last error code from DAQ_MCU: %w", err)
		return
	}
	m.LateFlag = iLate == 1
	//
	// Characterize the analog voltage scaling.
	//
	vrefV := 1.2
	countMax := 1 << 23
	m.FullScaleVoltage = make([]float64, m.NChannels)
	m.FullScaleCount = make([]int, m.NChannels)
	for ichip := 0; ichip < 4; ichip++ {
		for ichan := 0; ichan < 4; ichan++ {
			ach := 4*ichip + ichan
			if ach < m.NChannels {
				gain, _ := my.GetAnalogGain(ichip, ichan)
				m.FullScaleVoltage[ach] = vrefV / gain
				m.FullScaleCount[ach] = countMax
			}
		}
	}
	//
	return
}

type SampleSelection struct {
	PreTrigger int
	Total int
}

func (my *Pico2_DAQ_MCU) GetRecordedDataByIndex(ss *SampleSelection) (rec edaqs.Record, err error) {
	meta, err := my.GetRecordMetaData()
	if err != nil {
		err = fmt.Errorf("failed to get metadata for record: %w", err)
		return
	}
	nChannels := meta.NChannels
	//
	// By default, we return the entire record from the DAQ MCU.
	// When indexing by sample number, the AVR DAQ MCU always has
	// the oldest at index 0, even if it has a non-zero byte address
	// within its SRAM storage.
	firstSampleSelected := 0
	lastSampleSelected := meta.NSamplesInRecord
	nSamplesSelected := meta.NSamplesInRecord
	nSamplesPreTrigger := meta.NSamplesPreTrigger
	// We might want to adjust the selection of samples to be a subset of the full record.
	if ss != nil {
		if meta.Mode == IMMEDIATE {
			// For IMMEDIATE mode, the trigger sample is always at index zero.
			// There are no sample data at the other end of SRAM to wrap around.
			firstSampleSelected = 0
			lastSampleSelected = firstSampleSelected + ss.Total
			nSamplesSelected = ss.Total
			nSamplesPreTrigger = 0
		} else {
			// Because of potential wrap-around for other trigger modes,
			// it may be that the selected first-sample index is zero.
			// We will hanfle this wrap-around below.
			firstSampleSelected = meta.TriggerSample - ss.PreTrigger
			lastSampleSelected = firstSampleSelected + ss.Total
			nSamplesSelected = ss.Total
			nSamplesPreTrigger = ss.PreTrigger
		}
	}
	// Prepare the record of data that gets returned.
	rec = edaqs.Record{
		NChannels: nChannels,
		NSamplesInRecord: nSamplesSelected,
		NSamplesPreTrigger: nSamplesPreTrigger,
		DTmicroseconds: meta.DTmicroseconds,
		LateFlag: meta.LateFlag,
		LastErrorCode: meta.LastErrorCode,
		FullScaleVoltage: meta.FullScaleVoltage,
		FullScaleCount: meta.FullScaleCount,
	}
	rec.AllocateDataSpace(nChannels, nSamplesSelected)
	var sampleData []int
	wrapN := meta.MaxNSamples;
	// The first sample selected (the oldest) is assigned as (new) index zero.
	jj := 0
	for i := firstSampleSelected; i < lastSampleSelected; i++ {
		// We may need to unwrap the index.
		ii := i
		for ii < 0 {
			ii += wrapN
		}
		for ii >= wrapN {
			ii -= wrapN
		}
		sampleData, err = my.GetSampleSet(ii)
		if err != nil {
			err = fmt.Errorf("error while getting sample set %d: %v", i, err)
			break
		}
		for ach := 0; ach < nChannels; ach++ {
			rec.Data[ach][jj] = sampleData[ach]
		}
		jj += 1
	}
	return
}
