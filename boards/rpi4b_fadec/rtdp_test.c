
// rtdp_test.c
// Real-Time Data Port (RTDP) external master test - Raspberry Pi 4B
//
// Monitors DATA_RDY from the ADS131M04 DAQ board. On each rising edge, pulls
// CS low and bit-bangs a 16-byte SPI Mode 3 read (4 x int32_t big-endian).
// The RS-485 transceiver on the RPi side is kept in receive-only mode.
//
// Uses libgpiod v2 API.
//
// 2026-02-26 JM: Initial version

// HARDWARE PIN MAPPING
//   DRDY1  >  GPIO 2   (ADC1 DATA READY - input, rising-edge event)
//   MISO   >  GPIO 9   (SPI0 MISO       - input, data from ADC board via RS-485)
//   CLK    >  GPIO 11  (SPI0 SCLK       - output, idles HIGH for SPI Mode 3)
//   CS1    >  GPIO 13  (ADC1 CS         - output, active low)
//   DE     >  GPIO 24  (RTDP_DE  - output, HIGH = RPi RS-485 driver enabled)
//   REN    >  GPIO 25  (RTDP_REn - output, LOW  = RS-485 receiver enabled)

// BUILD COMMAND (ON Raspberry Pi 4B):
//  gcc -O2 -Wall -o rtdp_test rtdp_test.c -lgpiod
//  (run as root or with CAP_SYS_NICE + readable /dev/gpiomem)

// REQUIREMENTS:
//  sudo apt install libgpiod-dev

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <sys/mman.h>
#include <gpiod.h>

// ---------------------------------------------------------------------------
// BCM2711 (RPi 4B) direct GPIO register access via /dev/gpiomem.
// Each operation is a single register write/read — no syscall overhead.
// libgpiod is still used for GPIO setup and DRDY edge-event waiting.
// ---------------------------------------------------------------------------
#define GPIOMEM_PATH    "/dev/gpiomem"
#define GPIO_MAP_SIZE   0x1000u
// Register word-offsets from the GPIO peripheral base
#define GPSET0  (0x1Cu / 4u)   // Set   GPIO 0-31
#define GPCLR0  (0x28u / 4u)   // Clear GPIO 0-31
#define GPLEV0  (0x34u / 4u)   // Level GPIO 0-31

static volatile uint32_t *g_gpio = NULL;

#define GPIO_SET(pin)  (g_gpio[GPSET0] = (1u << (pin)))
#define GPIO_CLR(pin)  (g_gpio[GPCLR0] = (1u << (pin)))
#define GPIO_GET(pin)  ((g_gpio[GPLEV0] >> (pin)) & 1u)

// GPIO ASSIGNMENTS
#define GPIO_CHIP_PATH      "/dev/gpiochip0"
#define GPIO_DRDY1          2u      // ADC1 DATA READY (input, busy-polled via mmap)
#define GPIO_MISO           9u      // SPI0 MISO (input)
#define GPIO_CLK            11u     // SPI0 SCLK (output)
#define GPIO_CS1            13u     // ADC1 CS, active low (output)
#define GPIO_RTDP_DE        24u     // RS-485 Driver Enable (output)
#define GPIO_RTDP_REn       25u     // RS-485 Receiver Enable, active low (output)

// SPI timing: half-period in nanoseconds.
// Each half-cycle has ~125 ns of overhead (register ops + clock_gettime calls),
// so 125 ns delay gives ~250 ns actual half-period = ~2 MHz, matching the
// Pico2 SPI slave limit of 2 MHz.
#define SPI_HALF_PERIOD_NS  125L

// DATA_RDY busy-poll timeout: 5 seconds
#define DRDY_TIMEOUT_S      5

// RTDP payload: 4 channels × 4 bytes
#define RTDP_NUM_BYTES      16
#define RTDP_NUM_CHANNELS   4

#define CONSUMER            "rtdp_test"

// ---------------------------------------------------------------------------

static volatile int g_running = 1;

static void sigint_handler(int sig)
{
    (void)sig;
    g_running = 0;
}

// Busy-wait delay using CLOCK_MONOTONIC (no syscall sleep, PREEMPT_RT safe).
static inline void ns_delay(long ns)
{
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long target_ns = t0.tv_nsec + ns;
    long carry     = target_ns / 1000000000L;
    t0.tv_sec     += carry;
    t0.tv_nsec     = target_ns - carry * 1000000000L;
    do {
        clock_gettime(CLOCK_MONOTONIC, &t1);
    } while ((t1.tv_sec < t0.tv_sec) ||
             (t1.tv_sec == t0.tv_sec && t1.tv_nsec < t0.tv_nsec));
}

// ---------------------------------------------------------------------------
// SPI Mode 3 bit-bang receive (CPOL=1, CPHA=1) — direct BCM2711 register access.
//   Clock idles HIGH. Slave shifts data on falling edge; master samples on rising edge.
//   Uses g_gpio mmap registers: no syscalls during transfer (~1 ns per GPIO op).
//   Reads 'len' bytes MSB-first into buf[].
// ---------------------------------------------------------------------------
static void spi_read_bytes(uint8_t *buf, int len)
{
    for (int i = 0; i < len; i++) {
        uint8_t byte = 0;
        for (int bit = 7; bit >= 0; bit--) {
            // Falling edge: slave shifts new bit onto MISO
            GPIO_CLR(GPIO_CLK);
            ns_delay(SPI_HALF_PERIOD_NS);

            // Rising edge: sample MISO on the rising edge (SPI Mode 3, CPHA=1)
            GPIO_SET(GPIO_CLK);
            if (GPIO_GET(GPIO_MISO))
                byte |= (uint8_t)(1u << bit);
            ns_delay(SPI_HALF_PERIOD_NS);
        }
        buf[i] = byte;
    }
}

// ---------------------------------------------------------------------------
// Helper: build and submit a line request.
// Returns NULL on failure (settings/config objects are always freed).
// ---------------------------------------------------------------------------
static struct gpiod_line_request *request_lines(
        struct gpiod_chip *chip,
        const unsigned int *offsets, size_t num_offsets,
        struct gpiod_line_settings *settings)
{
    struct gpiod_line_config    *lcfg  = gpiod_line_config_new();
    struct gpiod_request_config *rcfg  = gpiod_request_config_new();
    struct gpiod_line_request   *req   = NULL;

    if (!lcfg || !rcfg)
        goto out;

    gpiod_request_config_set_consumer(rcfg, CONSUMER);

    if (gpiod_line_config_add_line_settings(lcfg, offsets,
                                            num_offsets, settings) < 0)
        goto out;

    req = gpiod_chip_request_lines(chip, rcfg, lcfg);

out:
    if (lcfg)  gpiod_line_config_free(lcfg);
    if (rcfg)  gpiod_request_config_free(rcfg);
    return req;
}

// ---------------------------------------------------------------------------

int main(void)
{
    signal(SIGINT, sigint_handler);

    int rc = EXIT_FAILURE;

    // -----------------------------------------------------------------------
    // PREEMPT_RT: elevate to SCHED_FIFO and lock all memory to prevent
    // page faults and scheduling latency during the bit-bang transfer.
    // -----------------------------------------------------------------------
    struct sched_param sp = { .sched_priority = 80 };
    if (sched_setscheduler(0, SCHED_FIFO, &sp) < 0) {
        perror("sched_setscheduler (need root or CAP_SYS_NICE)");
        // Non-fatal — continue without RT priority.
    }
    if (mlockall(MCL_CURRENT | MCL_FUTURE) < 0) {
        perror("mlockall");
        // Non-fatal — continue without memory locking.
    }

    // -----------------------------------------------------------------------
    // Map BCM2711 GPIO registers directly for zero-syscall bit-bang I/O.
    // -----------------------------------------------------------------------
    int gpiomem_fd = open(GPIOMEM_PATH, O_RDWR | O_SYNC);
    if (gpiomem_fd < 0) {
        perror("open /dev/gpiomem");
        return EXIT_FAILURE;
    }
    g_gpio = (volatile uint32_t *)mmap(NULL, GPIO_MAP_SIZE,
                                       PROT_READ | PROT_WRITE,
                                       MAP_SHARED, gpiomem_fd, 0);
    close(gpiomem_fd);
    if (g_gpio == MAP_FAILED) {
        perror("mmap /dev/gpiomem");
        return EXIT_FAILURE;
    }

    struct gpiod_chip         *chip     = NULL;
    struct gpiod_line_settings *s_hi    = NULL;  // output, initial HIGH
    struct gpiod_line_settings *s_lo    = NULL;  // output, initial LOW
    struct gpiod_line_settings *s_in    = NULL;  // plain input
    struct gpiod_line_request  *out_req = NULL;  // CLK, CS1, DE, REn
    struct gpiod_line_request  *in_req  = NULL;  // MISO + DRDY1

    chip = gpiod_chip_open(GPIO_CHIP_PATH);
    if (!chip) { perror("gpiod_chip_open"); goto cleanup; }

    // --- Output settings: HIGH initial (CLK idles HIGH = CPOL=1; CS deasserted) ---
    s_hi = gpiod_line_settings_new();
    if (!s_hi) goto cleanup;
    gpiod_line_settings_set_direction(s_hi, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(s_hi, GPIOD_LINE_VALUE_ACTIVE);

    // --- Output settings: LOW initial (DE=0; REn=0 = receiver enabled) ---
    s_lo = gpiod_line_settings_new();
    if (!s_lo) goto cleanup;
    gpiod_line_settings_set_direction(s_lo, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(s_lo, GPIOD_LINE_VALUE_INACTIVE);

    // Build combined output request (CLK + CS1 HIGH, DE + REn LOW)
    // We need separate settings per group: use two separate requests.
    {
        const unsigned int hi_offs[] = { GPIO_CLK, GPIO_CS1 };
        const unsigned int lo_offs[] = { GPIO_RTDP_DE, GPIO_RTDP_REn };

        // Build a single request covering all four output lines with mixed
        // initial values using one line_config with two settings entries.
        struct gpiod_line_config    *lcfg = gpiod_line_config_new();
        struct gpiod_request_config *rcfg = gpiod_request_config_new();
        if (!lcfg || !rcfg) {
            gpiod_line_config_free(lcfg);
            gpiod_request_config_free(rcfg);
            goto cleanup;
        }
        gpiod_request_config_set_consumer(rcfg, CONSUMER);
        gpiod_line_config_add_line_settings(lcfg, hi_offs, 2, s_hi);
        gpiod_line_config_add_line_settings(lcfg, lo_offs, 2, s_lo);
        out_req = gpiod_chip_request_lines(chip, rcfg, lcfg);
        gpiod_line_config_free(lcfg);
        gpiod_request_config_free(rcfg);
    }
    if (!out_req) { perror("request outputs"); goto cleanup; }

    // --- MISO + DRDY1: plain inputs (level read via mmap for zero-latency polling) ---
    s_in = gpiod_line_settings_new();
    if (!s_in) goto cleanup;
    gpiod_line_settings_set_direction(s_in, GPIOD_LINE_DIRECTION_INPUT);

    {
        const unsigned int offs[] = { GPIO_MISO, GPIO_DRDY1 };
        in_req = request_lines(chip, offs, 2, s_in);
    }
    if (!in_req) { perror("request MISO/DRDY inputs"); goto cleanup; }

    // Settings objects no longer needed after all requests are made
    gpiod_line_settings_free(s_hi);  s_hi  = NULL;
    gpiod_line_settings_free(s_lo);  s_lo  = NULL;
    gpiod_line_settings_free(s_in);  s_in  = NULL;

    printf("RTDP test started — DATA_RDY on GPIO %u, SPI Mode 3, mmap busy-poll\n",
           GPIO_DRDY1);
    printf("Press Ctrl+C to quit.\n\n");
    printf("%-10s  %-14s %-14s %-14s %-14s\n",
           "Sample", "CH1 (raw)", "CH2 (raw)", "CH3 (raw)", "CH4 (raw)");
    printf("%-10s  %-14s %-14s %-14s %-14s\n",
           "----------", "--------------", "--------------",
           "--------------", "--------------");

    uint64_t sample_count = 0;
    uint8_t  rx[RTDP_NUM_BYTES];

    while (g_running) {
        // Busy-poll for DATA_RDY rising edge via mmap'd GPIO registers.
        // libgpiod poll() has 100–300 µs kernel wakeup latency even on PREEMPT_RT,
        // which can exhaust the Pico's 500 µs CS-wait timeout before CS is asserted.
        // Direct register reads are ~1 ns each — latency is negligible.
        {
            struct timespec t_deadline;
            clock_gettime(CLOCK_MONOTONIC, &t_deadline);
            t_deadline.tv_sec += DRDY_TIMEOUT_S;

            // Step 1: wait for LOW so we catch a fresh rising edge
            while (GPIO_GET(GPIO_DRDY1)) {
                if (!g_running) goto done;
                struct timespec now;
                clock_gettime(CLOCK_MONOTONIC, &now);
                if (now.tv_sec > t_deadline.tv_sec ||
                    (now.tv_sec == t_deadline.tv_sec &&
                     now.tv_nsec >= t_deadline.tv_nsec)) {
                    printf("  [timeout: DATA_RDY stuck HIGH after %d s]\n",
                           DRDY_TIMEOUT_S);
                    goto next_sample;
                }
            }

            // Step 2: wait for HIGH (the rising edge)
            while (!GPIO_GET(GPIO_DRDY1)) {
                if (!g_running) goto done;
                struct timespec now;
                clock_gettime(CLOCK_MONOTONIC, &now);
                if (now.tv_sec > t_deadline.tv_sec ||
                    (now.tv_sec == t_deadline.tv_sec &&
                     now.tv_nsec >= t_deadline.tv_nsec)) {
                    printf("  [timeout: no DATA_RDY after %d s]\n",
                           DRDY_TIMEOUT_S);
                    goto next_sample;
                }
            }
        }

        // Enable RPi RS-485 driver so CLK and CS reach the Pico over the bus.
        // REn stays LOW (receiver always enabled to read MISO back).
        GPIO_SET(GPIO_RTDP_DE);

        // Assert CS (active low) — signals Pico Core 1 to enable its RS-485 TX driver.
        GPIO_CLR(GPIO_CS1);
        // Busy-wait for Pico Core 1 to detect CSn low and raise its DE.
        // Core 1 poll latency + gpio_put(DE) + ISL83491 propagation is well under 5 µs;
        // 10 µs gives comfortable margin without the scheduler jitter of usleep().
        ns_delay(10000L);

        // Read 16 bytes via direct-register bit-bang SPI Mode 3.
        // Pico is the sole driver of MISO; RPi receiver (REn=LOW) listens.
        spi_read_bytes(rx, RTDP_NUM_BYTES);

        // Deassert CS, then disable RPi RS-485 driver.
        GPIO_SET(GPIO_CS1);
        GPIO_CLR(GPIO_RTDP_DE);

        // Decode 4 × int32_t big-endian
        int32_t samples[RTDP_NUM_CHANNELS];
        for (int ch = 0; ch < RTDP_NUM_CHANNELS; ch++) {
            int idx = ch * 4;
            uint32_t raw = ((uint32_t)rx[idx + 0] << 24) |
                           ((uint32_t)rx[idx + 1] << 16) |
                           ((uint32_t)rx[idx + 2] <<  8) |
                           ((uint32_t)rx[idx + 3]);
            samples[ch] = (int32_t)raw;
        }

        sample_count++;
        printf("%-10llu  %-14d %-14d %-14d %-14d\n",
               (unsigned long long)sample_count,
               samples[0], samples[1], samples[2], samples[3]);
        continue;
    next_sample:;
    }
    done:

    // Safe shutdown: restore idle states
    GPIO_SET(GPIO_CS1);         // CS deasserted
    GPIO_SET(GPIO_CLK);         // CLK idle HIGH (CPOL=1)
    GPIO_CLR(GPIO_RTDP_DE);     // RPi RS-485 driver disabled
    // REn (GPIO 25) stays LOW via libgpiod-managed request — leave as-is
    gpiod_line_request_set_value(out_req, GPIO_RTDP_REn, GPIOD_LINE_VALUE_INACTIVE);

    rc = EXIT_SUCCESS;
    printf("\nRTDP test stopped. %llu sample(s) received.\n",
           (unsigned long long)sample_count);

cleanup:
    if (in_req)   gpiod_line_request_release(in_req);
    if (out_req)  gpiod_line_request_release(out_req);
    if (s_hi)     gpiod_line_settings_free(s_hi);
    if (s_lo)     gpiod_line_settings_free(s_lo);
    if (s_in)     gpiod_line_settings_free(s_in);
    if (chip)     gpiod_chip_close(chip);
    if (g_gpio && g_gpio != MAP_FAILED)
        munmap((void *)g_gpio, GPIO_MAP_SIZE);
    return rc;
}