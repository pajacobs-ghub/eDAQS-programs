// file: avr64ea28_daq_mcu.go
// Service functions for the AVR64EA28 DAQ MCU.
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package avr64ea28_daq_mcu

import (
	"fmt"
	"strconv"
	"strings"
	comms "example.com/edaqs/pic18f16q41_comms_1"
)


type AVR_DAQ_MCU struct {
	comms_mcu *comms.COMMS_1_MCU
}

func NewAVR_DAQ_MCU(comms_mcu *comms.COMMS_1_MCU) *AVR_DAQ_MCU {
	return &AVR_DAQ_MCU{
		comms_mcu: comms_mcu,
	}
}

func (my *AVR_DAQ_MCU) GetVersion() (resp []byte, err error) {
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("v"))
	return
}

func (my *AVR_DAQ_MCU) GetNRegActual() (nreg uint, err error) {
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte("n"))
	if err == nil {
		_, err = fmt.Sscanf(string(resp), "%d", &nreg)
	}
	return
}

func (my *AVR_DAQ_MCU) SetRegistersToFactoryValues() (err error) {
	_, err = my.comms_mcu.Command_DAQ_MCU([]byte("F"))
	return
}

func (my *AVR_DAQ_MCU) GetRegValue(i RegIndex) (val int, err error) {
	cmd := fmt.Sprintf("r %d", i)
	var resp []byte
	resp, err = my.comms_mcu.Command_DAQ_MCU([]byte(cmd))
	if err == nil {
		_, err = fmt.Sscanf(string(resp), "%d", &val)
	}
	return
}

func (my *AVR_DAQ_MCU) GetRegValues(indices []RegIndex) (vals []int, err error) {
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

func (my *AVR_DAQ_MCU) GetAllRegValuesAsString() (vals string, err error) {
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

func (my *AVR_DAQ_MCU) SetRegValue(i RegIndex, val int) (err error) {
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

func (my *AVR_DAQ_MCU) SetRegValues(pairs map[RegIndex]int) (err error) {
	for i, val := range pairs {
		err = my.SetRegValue(i, val)
		if err != nil {
			err = fmt.Errorf("error while setting reg[%d]: %w", i, err)
			return
		}
	}
	return
}

// Sets the AVR ticks register to (approximately) achieve
// the sample period in microseconds.
func (my *AVR_DAQ_MCU) SetSamplePeriod_us(dt int) (err error) {
	ticks := int(float64(dt) / US_PER_TICK)
	err = my.SetRegValue(PER_TICKS, ticks)
	return
}

func (my *AVR_DAQ_MCU) GetSamplePeriod_us() (dt float64, err error) {
	ticks, err := my.GetRegValue(PER_TICKS)
	if err != nil {
		err = fmt.Errorf("failed to read PER_TICKS register: %w", err)
		return
	}
	dt = float64(ticks) * US_PER_TICK
	return
}

func (my *AVR_DAQ_MCU) SetAnalogChannels(pairs map[RegIndex]InputPin) (err error) {
	for i, val := range pairs {
		err = my.SetRegValue(i, int(val))
		if err != nil {
			err = fmt.Errorf("error while setting channel %v to input %v: %w", i, val, err)
			return
		}
	}
	return
}

func (my *AVR_DAQ_MCU) SetPGA(gain PGAGain) (err error) {
	// Route analog signal via PGA.
	err = my.SetRegValue(PGA_FLAG, 1)
	if err != nil {
		err = fmt.Errorf("error setting PGA_FLAG register: %w", err)
		return
	}
	err = my.SetRegValue(PGA_GAIN, int(gain))
	if err != nil {
		err = fmt.Errorf("error setting PGA_GAIN register: %w", err)
		return
	}
	return
}

func (my *AVR_DAQ_MCU) ClearPGA() (err error) {
	// Sample analog signal without PGA.
	err = my.SetRegValue(PGA_FLAG, 0)
	if err != nil {
		err = fmt.Errorf("error setting PGA_FLAG register: %w", err)
		return
	}
	err = my.SetRegValue(PGA_GAIN, int(X1))
	if err != nil {
		err = fmt.Errorf("error setting PGA_GAIN register: %w", err)
		return
	}
	return
}

func (my *AVR_DAQ_MCU) GetAnalogGain() (gain PGAGain, err error) {
	pgaFlag, err := my.GetRegValue(PGA_FLAG)
	if err != nil {
		err = fmt.Errorf("error reading PGA_FLAG register: %w", err)
		return
	}
	if pgaFlag == 0 {
		gain = X1
		return
	}
	g, err := my.GetRegValue(PGA_GAIN)
	if err != nil {
		err = fmt.Errorf("error reading PGA_GAIN register: %w", err)
		return
	}
	gain = PGAGain(g)
	return
}

func (my *AVR_DAQ_MCU) SetAnalogRefVoltage(v RefVoltage) (err error) {
	err = my.SetRegValue(V_REF, int(v))
	if err != nil {
		err = fmt.Errorf("error setting V_REF register: %w", err)
		return
	}
	return
}

func (my *AVR_DAQ_MCU) GetAnalogRefVoltage() (vref RefVoltage, err error) {
	var v int
	v, err = my.GetRegValue(V_REF)
	if err != nil {
		err = fmt.Errorf("error reading V_REF register: %w", err)
		return
	}
	vref = RefVoltage(v)
	return
}

// The number of analog samples per conversion result is 2**n.
//
// Note that when setting this number nonzero,
// we will get conversion results that are 16 times
// the nominal 12-bit value because we have elected
// to use burst-mode with result scaling.
func (my *AVR_DAQ_MCU) SetBurst(acc SampleAccumulation) (err error) {
	err = my.SetRegValue(NBURST, int(acc))
	if err != nil {
		err = fmt.Errorf("error setting NBURST register: %w", err)
		return
	}
	return
}

func (my *AVR_DAQ_MCU) GetBurst() (acc SampleAccumulation, err error) {
	i, err := my.GetRegValue(NBURST)
	if err != nil {
		err = fmt.Errorf("error reading NBURST register: %w", err)
		return
	}
	acc = SampleAccumulation(i)
	return
}

func (my *AVR_DAQ_MCU) SetDifferentialConversion() (err error) {
	err = my.SetRegValue(DIFF_CONV, 1)
	if err != nil {
		err = fmt.Errorf("error while trying to set differential conversion: %w", err)
		return
	}
	return
}

func (my *AVR_DAQ_MCU) SetSingleSidedConversion() (err error) {
	err = my.SetRegValue(DIFF_CONV, 0)
	if err != nil {
		err = fmt.Errorf("error while trying to set single-sided conversion: %w", err)
		return
	}
	return
}

func (my *AVR_DAQ_MCU) ImmediateSampleSet() (vals []int, err error) {
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
func (my *AVR_DAQ_MCU) SetTriggerImmediate() (err error) {
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
func (my *AVR_DAQ_MCU) SetTriggerInternal(channel int, level int, slope TriggerSlope) (err error) {
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
func (my *AVR_DAQ_MCU) SetTriggerExternal() (err error) {
	err = my.SetRegValue(TRIG_MODE, int(EXTERNAL))
	return
}

func (my *AVR_DAQ_MCU) GetTriggerMode() (m TriggerMode, err error) {
	var i int
	i, err = my.GetRegValue(TRIG_MODE)
	m = TriggerMode(i)
	return
}

// NSAMPLES is the number of samples to be recorded after trigger event.
func (my *AVR_DAQ_MCU) SetNSamples(n int) (err error) {
	if n < 0 {
		// Somewhat arbitrary.
		n = 100
	}
	// The AVR firmware reports this value as a 16-bit signed integer,
	// so let's avoid setting values too large.
	if n > 32767 {
		n = 32767
	}
	err = my.SetRegValue(NSAMPLES, n)
	return
}

func (my *AVR_DAQ_MCU) GetNSamples() (n int, err error) {
	n, err = my.GetRegValue(NSAMPLES)
	return
}

// What happens after calling this function depends on the register settings
// and, maybe, the external signals.
func (my *AVR_DAQ_MCU) StartSampling() (err error) {
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
func (my *AVR_DAQ_MCU) GetSampleSet(i int) (vals []int, err error) {
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
