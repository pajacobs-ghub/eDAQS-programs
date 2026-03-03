# RASPBERRY PI 4B FADEC

## Compatible Boards and Firmware
**ADS131M04 4-Channel 24-bit ADC DAQ Board**
**Version:** v0.44 (2026-01-08)  
**MCU:** Raspberry Pi Pico 2 (RP2350)  
**ADC:** Texas Instruments ADS131M04


## ADC Board Real-Time Data Port (RTDP) Implementation
The **Real-Time Data Port** is a dedicated, ultra-low-latency streaming interface that gives an external supervisor device (PC, another MCU, FPGA, etc.) instant access to the **most recent 4-channel ADC sample set** while the main high-speed sampling runs uninterrupted on Core 0.

It is designed for applications that need a continuous live view of the analog data without polling the large circular buffer in SRAM.


### Key Features
- Runs entirely on **Core 1** — zero impact on Core 0 sampling timing.
- Uses **DMA** for zero-CPU-overhead SPI transfers.
- Always delivers the **freshest** sample (4 × 32-bit signed integers).
- Data format: **16 bytes, big-endian**.
- Non-blocking with configurable timeout protection.
- Enabled/disabled via virtual register 7 (`vregister[7]` = advertising period in µs).
- Robust: automatically de-initialises SPI if the external master disappears.


### Hardware Pins & Required Circuitry
| GPIO | Pin Name       | Direction | Function                              | Notes |
|------|----------------|-----------|---------------------------------------|-------|
| 17   | SPI0_CSn       | Input     | Chip Select (active low)              | Pulled up on Pico2 |
| 18   | SPI0_SCK       | Input     | Serial Clock                          | Pulled up on Pico2 |
| 19   | SPI0_TX (MISO) | Output    | Data output to external master        | **Main data line** |
| 27   | DATA_RDY       | Output    | New data available signal             | Goes high when fresh data is ready |
| 20   | RTDP_DE        | Output    | RS-485 Driver Enable                  | High = transmit |
| 21   | RTDP_REn       | Output    | RS-485 Receiver Enable (active low)   | Low = receive enabled |


### FADEC External Hardware
- **ISL83491 transceiver**
  - Pico GPIO19 > DI (driver input)
  - Transceiver A/B differential pair > FADEC master
  - DE > GPIO20
  - /RE > GPIO21

**SPI Mode:** Mode 3 (CPOL=1, CPHA=1)  
**Max clock:** 2 MHz (recommended)

### How the RTDP Works

**Core 0 (sampling loop):**
- Every new ADC sample set is stored in the circular buffer.
- If RTDP is enabled and Core 1 is idle, copy latest 4 samples to shared buffer and notify Core 1.

**Core 1 (RTDP service):**
1. Receives notification.
2. Packs data into 16-byte big-endian buffer.
3. (Re)initialises SPI0 as slave if necessary.
4. Sets up TX + RX DMA channels.
5. Asserts **DATA_RDY** (GPIO27 = 1).
6. Starts DMA transfer.
7. Waits for external master to pull **CSn** low.
8. Enables RS-485 transceiver.
9. Waits for full transfer + CSn release.
10. Disables transceiver, clears DATA_RDY, returns to idle.

If the external master does **not** respond within the timeout (`vregister[7]`), the port safely aborts and cleans up.

### Example External Master Sequence

```c
// Pseudo-code for external device
while (true) {
    if (DATA_RDY == HIGH) {
        pull CSn LOW;
        // Clock out exactly 16 bytes (SPI Mode 3, up to 2 MHz)
        uint8_t rx[16];
        spi_transfer(rx, 16);   // dummy TX bytes are ignored
        release CSn;
        process_live_data(rx);  // 4 × int32_t big-endian
    }
}