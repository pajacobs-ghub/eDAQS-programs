// file: avr64ea28_daq_mcu.go
// Service functions for the AVR64EA28 DAQ MCU.
//
// Peter J.
// 2026-09-22: Started rebuilding from the Python functions.
//

package edaqs

import (
	_ "bufio"
	_ "bytes"
	"fmt"
	_ "go.bug.st/serial"
	_ "log"
)

type RegIndex uint

const (
	NReg = 36
	PER_TICKS RegIndex = 0
	NCHANNELS RegIndex = 1
	NSAMPLES RegIndex = 2
	TRIG_MODE RegIndex = 3
	TRIG_CHAN RegIndex = 4
	TRIG_LEVEL RegIndex = 5
	TRIG_SLOPE RegIndex = 6
	PGA_FLAG RegIndex = 7
	PGA_GAIN RegIndex = 8
	V_REF RegIndex = 9
	CH0P RegIndex = 10
	CH0N RegIndex = 11
	CH1P RegIndex = 12
	CH1N RegIndex = 13
	CH2P RegIndex = 14
	CH2N RegIndex = 15
	CH3P RegIndex = 16
	CH3N RegIndex = 17
	CH4P RegIndex = 18
	CH4N RegIndex = 19
	CH5P RegIndex = 20
	CH5N RegIndex = 21
	CH6P RegIndex = 22
	CH6N RegIndex = 23
	CH7P RegIndex = 24
	CH7N RegIndex = 25
	CH8P RegIndex = 26
	CH8N RegIndex = 27
	CH9P RegIndex = 28
	CH9N RegIndex = 29
	CH10P RegIndex = 30
	CH10N RegIndex = 31
	CH11P RegIndex = 32
	CH11N RegIndex = 33
	NBURST RegIndex = 34
	DIFF_CONV RegIndex = 35
)

func (i RegIndex) String() string {
	switch i {
	case PER_TICKS: return "PER_TICKS"
	case NCHANNELS: return "NCHANNELS"
	case NSAMPLES: return "NSAMPLES"
	case TRIG_MODE: return "TRIG_MODE"
	case TRIG_CHAN: return "TRIG_CHAN"
	case TRIG_LEVEL: return "TRIG_LEVEL"
	case TRIG_SLOPE: return "TRIG_SLOPE"
	case PGA_FLAG: return "PGA_FLAG"
	case PGA_GAIN: return "PGA_GAIN"
	case V_REF: return "V_REF"
	case CH0P: return "CH0+"
	case CH0N: return "CH0-"
	case CH1P: return "CH1+"
	case CH1N: return "CH1-"
	case CH2P: return "CH2+"
	case CH2N: return "CH2-"
	case CH3P: return "CH3+"
	case CH3N: return "CH3-"
	case CH4P: return "CH4+"
	case CH4N: return "CH4-"
	case CH5P: return "CH5+"
	case CH5N: return "CH5-"
	case CH6P: return "CH6+"
	case CH6N: return "CH6-"
	case CH7P: return "CH7+"
	case CH7N: return "CH7-"
	case CH8P: return "CH8+"
	case CH8N: return "CH8-"
	case CH9P: return "CH9+"
	case CH9N: return "CH9-"
	case CH10P: return "CH10+"
	case CH10N: return "CH10-"
	case CH11P: return "CH11+"
	case CH11N: return "CH11-"
	case NBURST: return "NBURST"
	case DIFF_CONV: return "DIFF_CONV"
	}
	return "UNKNOWN"
}

type InputPin uint

const (
	AIN28 InputPin = 28
	AIN29 InputPin = 29
	AIN30 InputPin = 30
	AIN31 InputPin = 31
	AIN0 InputPin = 0
	AIN1 InputPin = 1
	AIN2 InputPin = 2
	AIN3 InputPin = 3
	AIN4 InputPin = 4
	AIN5 InputPin = 5
	AIN6 InputPin = 6
	AIN7 InputPin = 7
	GND InputPin = 48
)

func (i InputPin) String() string {
	switch i {
	case AIN28: return "AIN28"
	case AIN29: return "AIN29"
	case AIN30: return "AIN30"
	case AIN31: return "AIN31"
	case AIN0: return "AIN0"
	case AIN1: return "AIN1"
	case AIN2: return "AIN2"
	case AIN3: return "AIN3"
	case AIN4: return "AIN4"
	case AIN5: return "AIN5"
	case AIN6: return "AIN6"
	case AIN7: return "AIN7"
	case GND: return "GND"
	}
	return "UNKNOWN_PIN"
}

type PGAGain uint

const (
	X1 PGAGain = 0
	X2 PGAGain = 1
	X4 PGAGain = 2
	X8 PGAGain = 3
	X16 PGAGain = 4
)

func (i PGAGain) String() string {
	switch i {
	case X1: return "X1"
	case X2: return "X2"
	case X4: return "X4"
	case X8: return "X8"
	case X16: return "X16"
	}
	return "UNKNOWN_PGAGain"
}

type SampleAccumulation uint

const (
	ACC0 SampleAccumulation = 0
	ACC2 SampleAccumulation = 1
	ACC4 SampleAccumulation = 2
	ACC8 SampleAccumulation = 3
	ACC16 SampleAccumulation = 4
	ACC32 SampleAccumulation = 5
	ACC64 SampleAccumulation = 6
	ACC128 SampleAccumulation = 7
	ACC256 SampleAccumulation = 8
	ACC512 SampleAccumulation = 9
	ACC1024 SampleAccumulation = 10
)

func (i SampleAccumulation) String() string {
	switch i {
	case ACC0: return "NONE"
	case ACC2: return "ACC2"
	case ACC4: return "ACC4"
	case ACC8: return "ACC8"
	case ACC16: return "ACC16"
	case ACC32: return "ACC32"
	case ACC64: return "ACC64"
	case ACC128: return "ACC128"
	case ACC256: return "ACC256"
	case ACC512: return "ACC512"
	case ACC1024: return "ACC1024"
	}
	return "UNKNOWN_SampleAccumulation"
}

type RefVoltage uint

const (
	Vref4750 RefVoltage = 0
	Vref1024 RefVoltage = 1
	Vref2048 RefVoltage = 2
	Vref4096 RefVoltage = 3
	Vref2500 RefVoltage = 4
)

func (i RefVoltage) String() string {
	switch i {
	case Vref4750: return "4750mV"
	case Vref1024: return "1024mV"
	case Vref2048: return "2048mV"
	case Vref4096: return "4096mV"
	case Vref2500: return "2500mV"
	}
	return "UNKNOWN_Vref"
}

type TriggerMode uint

const (
	IMMEDIATE TriggerMode = 0
	INTERNAL TriggerMode = 1
	EXTERNAL TriggerMode = 2
)

func (i TriggerMode) String() string {
	switch i {
	case IMMEDIATE: return "IMMEDIATE"
	case INTERNAL: return "INTERNAL"
	case EXTERNAL: return "EXTERNAL"
	}
	return "UNKNOWN_TriggerMade"
}

type TriggerSlope uint

const (
	SLOPE_POS TriggerSlope = 0
	SLOPE_NEG TriggerSlope = 1
)

func (i TriggerSlope) String() string {
	switch i {
	case SLOPE_POS: return "POS"
	case SLOPE_NEG: return "NEG"
	}
	return "UNKNOWN_TriggerSlope"
}

const (
	// Hardware timer set at the following value.
	US_PER_TICK = 0.8
)


type AVR_DAQ_MCU struct {
	comms_mcu *COMMS_1_MCU
}

func NewAVR_DAQ_MCU(comms_mcu *COMMS_1_MCU) *AVR_DAQ_MCU {
	return &AVR_DAQ_MCU{
		comms_mcu: comms_mcu,
	}
}

func (my *AVR_DAQ_MCU) GetVersion() (resp []byte, err error) {
	resp, err = my.comms_mcu.command_DAQ_MCU([]byte("v"))
	return
}

func (my *AVR_DAQ_MCU) GetNRegActual() (nreg uint, err error) {
	var resp []byte
	resp, err = my.comms_mcu.command_DAQ_MCU([]byte("n"))
	if err == nil {
		_, err = fmt.Sscanf(string(resp), "%d", &nreg)
	}
	return
}
