// file: symbols.go
// Constants defined for the Pico2_DAQ_MCU service functions.
//

package pico2_daq_4x_ads131m04

import (
	"fmt"
)

type RegIndex uint

const NReg = 25

const (
	MCLK_KHZ RegIndex = 0
	OSR_SELECT RegIndex = 1
	PWR_SELECT RegIndex = 2
	NCHANNELS RegIndex = 3
	NSAMPLES RegIndex = 4
	TRIG_MODE RegIndex = 5
	TRIG_CHAN RegIndex = 6
	TRIG_LEVEL RegIndex = 7
	TRIG_SLOPE RegIndex = 8
	GAIN_AIN0_0 RegIndex = 9
	GAIN_AIN1_0 RegIndex = 10
	GAIN_AIN2_0 RegIndex = 11
	GAIN_AIN3_0 RegIndex = 12
	GAIN_AIN0_1 RegIndex = 13
	GAIN_AIN1_1 RegIndex = 14
	GAIN_AIN2_1 RegIndex = 15
	GAIN_AIN3_1 RegIndex = 16
	GAIN_AIN0_2 RegIndex = 17
	GAIN_AIN1_2 RegIndex = 18
	GAIN_AIN2_2 RegIndex = 19
	GAIN_AIN3_2 RegIndex = 20
	GAIN_AIN0_3 RegIndex = 21
	GAIN_AIN1_3 RegIndex = 22
	GAIN_AIN2_3 RegIndex = 23
	GAIN_AIN3_3 RegIndex = 24
)

func (i RegIndex) String() string {
	switch i {
	case MCLK_KHZ: return "MCLK_KHZ"
	case OSR_SELECT: return "OSR_SELECT"
	case PWR_SELECT: return "PWR_SELECT"
	case NCHANNELS: return "NCHANNELS"
	case NSAMPLES: return "NSAMPLES"
	case TRIG_MODE: return "TRIG_MODE"
	case TRIG_CHAN: return "TRIG_CHAN"
	case TRIG_LEVEL: return "TRIG_LEVEL"
	case TRIG_SLOPE: return "TRIG_SLOPE"
	case GAIN_AIN0_0: return "GAIN_AIN0_0"
	case GAIN_AIN1_0: return "GAIN_AIN1_0"
	case GAIN_AIN2_0: return "GAIN_AIN2_0"
	case GAIN_AIN3_0: return "GAIN_AIN3_0"
	case GAIN_AIN0_1: return "GAIN_AIN0_1"
	case GAIN_AIN1_1: return "GAIN_AIN1_1"
	case GAIN_AIN2_1: return "GAIN_AIN2_1"
	case GAIN_AIN3_1: return "GAIN_AIN3_1"
	case GAIN_AIN0_2: return "GAIN_AIN0_2"
	case GAIN_AIN1_2: return "GAIN_AIN1_2"
	case GAIN_AIN2_2: return "GAIN_AIN2_2"
	case GAIN_AIN3_2: return "GAIN_AIN3_2"
	case GAIN_AIN0_3: return "GAIN_AIN0_3"
	case GAIN_AIN1_3: return "GAIN_AIN1_3"
	case GAIN_AIN2_3: return "GAIN_AIN2_3"
	case GAIN_AIN3_3: return "GAIN_AIN3_3"
	}
	return "UNKNOWN"
}

type OSRSelect uint

const (
	OSR_128 OSRSelect = 0
	OSR_256 OSRSelect = 1
	OSR_512 OSRSelect = 2
	OSR_1024 OSRSelect = 3
	OSR_2048 OSRSelect = 4
	OSR_4096 OSRSelect = 5
	OSR_8192 OSRSelect = 6
	OSR_16384 OSRSelect = 7
)

func (i OSRSelect) Int() int {
	switch i {
	case OSR_128: return 128
	case OSR_256: return 256
	case OSR_512: return 512
	case OSR_1024: return 1024
	case OSR_2048: return 2048
	case OSR_4096: return 4096
	case OSR_8192: return 8192
	case OSR_16384: return 16384
	}
	return -1
}

func (i OSRSelect) String() string {
	return fmt.Sprintf("%d", i.Int())
}

type PowerSelect uint

const (
	VERY_LOW_POWER PowerSelect = 0
	LOW_POWER PowerSelect = 1
	HIGH_RESOLUTION PowerSelect = 2
)

func (i PowerSelect) String() string {
	switch i {
	case VERY_LOW_POWER: return "VERY_LOW_POWER"
	case LOW_POWER: return "LOW_POWER"
	case HIGH_RESOLUTION: return "HIGH_RESOLUTION"
	}
	return "UNKNOWN"
}

type PGAGain uint

const (
	X1 PGAGain = 0
	X2 PGAGain = 1
	X4 PGAGain = 2
	X8 PGAGain = 3
	X16 PGAGain = 4
	X32 PGAGain = 5
	X64 PGAGain = 6
	X128 PGAGain = 7
)

func (i PGAGain) Float() float64 {
	switch i {
	case X1: return 1.0
	case X2: return 2.0
	case X4: return 4.0
	case X8: return 8.0
	case X16: return 16.0
	case X32: return 32.0
	case 64: return 64.0
	case 128: return 128.0
	}
	return -1
}

func (i PGAGain) String() string {
	return fmt.Sprintf("%g", i.Float())
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
	return "UNKNOWN_TriggerMode"
}

type TriggerSlope uint

const (
	SLOPE_NEG TriggerSlope = 0
	SLOPE_POS TriggerSlope = 1
)

func (i TriggerSlope) String() string {
	switch i {
	case SLOPE_POS: return "POS"
	case SLOPE_NEG: return "NEG"
	}
	return "UNKNOWN_TriggerSlope"
}
