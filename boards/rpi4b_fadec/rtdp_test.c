/*
 * rtdp_test.c — 74HC165 "Data Ready" monitor on Raspberry Pi 4B
 *
 * The 74HC165 is wired as a parallel-in / serial-out shift register that
 * buffers "data ready" signals from downstream ADC channels.
 *
 * Pin mapping
 * -----------
 *   74HC165 SH/LD  →  GPIO 4   (active-low latch / "CS")
 *   74HC165 CLK    →  GPIO 11  (SPI0 SCLK)
 *   74HC165 Q7     →  GPIO 9   (SPI0 MISO)
 *
 * The byte is clocked out MSB-first (D7 first, D0 last).
 * We watch for D6 transitioning LOW → HIGH and print a timestamped message.
 *
 * Build
 * -----
 *   gcc -O2 -Wall -o rtdp_test rtdp_test.c -lgpiod
 *
 * Requires libgpiod v2.x:
 *   sudo apt install libgpiod-dev
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>
#include <gpiod.h>

/* ── GPIO assignments ─────────────────────────────────────────────────────── */
#define GPIO_CHIP_PATH  "/dev/gpiochip0"
#define GPIO_CLK        11u     /* SCLK  — drives the 74HC165 clock input    */
#define GPIO_MISO       9u      /* Q7    — serial output of the 74HC165       */
#define GPIO_SH_LD      4u      /* SH/LD — LOW latches parallel inputs        */

/* ── Bit of interest ─────────────────────────────────────────────────────── */
#define D6_MASK         (1u << 6)   /* bit 6 of the reconstructed byte       */

/* ── Polling interval between reads (microseconds) ──────────────────────── */
#define POLL_INTERVAL_US   100u

/* ── libgpiod v2 handles ─────────────────────────────────────────────────── */
static struct gpiod_chip            *chip;
static struct gpiod_line_request    *request;
static struct gpiod_line_settings   *out_settings;
static struct gpiod_line_settings   *in_settings;
static struct gpiod_line_config     *line_cfg;
static struct gpiod_request_config  *req_cfg;

static volatile sig_atomic_t running = 1;

/* ─────────────────────────────────────────────────────────────────────────── */

static void handle_sigint(int sig)
{
    (void)sig;
    running = 0;
}

static inline void delay_us(unsigned int us)
{
    struct timespec ts = {
        .tv_sec  = 0,
        .tv_nsec = (long)us * 1000L,
    };
    nanosleep(&ts, NULL);
}

static inline void set_line(unsigned int offset, int high)
{
    gpiod_line_request_set_value(request, offset,
        high ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE);
}

static inline int get_line(unsigned int offset)
{
    return gpiod_line_request_get_value(request, offset) == GPIOD_LINE_VALUE_ACTIVE
           ? 1 : 0;
}

/*
 * hc165_read_byte()
 *
 * Timing diagram (SH/LD active-low load, shift on CLK rising edge):
 *
 *   SH/LD  ‾‾\_/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
 *   CLK    ____/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_
 *   Q7     [D7] [D6] [D5] [D4] [D3] [D2] [D1] [D0]
 *
 * Q7 presents D7 immediately after SH/LD goes HIGH.
 * Each CLK rising edge shifts the next bit onto Q7.
 */
static uint8_t hc165_read_byte(void)
{
    uint8_t byte = 0;

    /* Pulse SH/LD LOW to latch all parallel inputs into the shift register */
    set_line(GPIO_SH_LD, 0);
    delay_us(1);
    set_line(GPIO_SH_LD, 1);
    delay_us(1);

    /*
     * Clock out 8 bits, MSB (D7) first.
     * Read Q7 before each rising clock edge — D7 is already on Q7 after
     * the latch pulse, and each rising edge advances the shift register
     * so the next bit is ready for the following read.
     */
    for (int i = 7; i >= 0; i--) {
        byte |= (uint8_t)(get_line(GPIO_MISO) << i);

        /* Rising edge: shift register advances, next bit appears on Q7 */
        set_line(GPIO_CLK, 1);
        delay_us(1);
        set_line(GPIO_CLK, 0);
        delay_us(1);
    }

    return byte;
}

/* ─────────────────────────────────────────────────────────────────────────── */

static int gpio_init(void)
{
    chip = gpiod_chip_open(GPIO_CHIP_PATH);
    if (!chip) {
        perror("gpiod_chip_open");
        return -1;
    }

    /* Output settings: CLK and SH/LD — both start inactive (LOW) */
    out_settings = gpiod_line_settings_new();
    if (!out_settings) goto err_chip;
    gpiod_line_settings_set_direction(out_settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(out_settings, GPIOD_LINE_VALUE_INACTIVE);

    /* Input settings: MISO (Q7) */
    in_settings = gpiod_line_settings_new();
    if (!in_settings) goto err_out_settings;
    gpiod_line_settings_set_direction(in_settings, GPIOD_LINE_DIRECTION_INPUT);

    /* Build the line config */
    line_cfg = gpiod_line_config_new();
    if (!line_cfg) goto err_in_settings;

    {
        unsigned int out_offsets[] = { GPIO_CLK, GPIO_SH_LD };
        if (gpiod_line_config_add_line_settings(line_cfg, out_offsets, 2,
                                                out_settings) < 0) {
            perror("gpiod_line_config_add_line_settings (outputs)");
            goto err_line_cfg;
        }
    }
    {
        unsigned int in_offsets[] = { GPIO_MISO };
        if (gpiod_line_config_add_line_settings(line_cfg, in_offsets, 1,
                                                in_settings) < 0) {
            perror("gpiod_line_config_add_line_settings (input)");
            goto err_line_cfg;
        }
    }

    /* Request config */
    req_cfg = gpiod_request_config_new();
    if (!req_cfg) goto err_line_cfg;
    gpiod_request_config_set_consumer(req_cfg, "rtdp_test");

    /* Acquire all three lines in one request */
    request = gpiod_chip_request_lines(chip, req_cfg, line_cfg);
    if (!request) {
        perror("gpiod_chip_request_lines");
        goto err_req_cfg;
    }

    /* Explicitly set CLK low, SH/LD high (shift / idle state) */
    set_line(GPIO_CLK,   0);
    set_line(GPIO_SH_LD, 1);

    return 0;

err_req_cfg:       gpiod_request_config_free(req_cfg);
err_line_cfg:      gpiod_line_config_free(line_cfg);
err_in_settings:   gpiod_line_settings_free(in_settings);
err_out_settings:  gpiod_line_settings_free(out_settings);
err_chip:          gpiod_chip_close(chip);
    return -1;
}

static void gpio_cleanup(void)
{
    if (request)      gpiod_line_request_release(request);
    if (req_cfg)      gpiod_request_config_free(req_cfg);
    if (line_cfg)     gpiod_line_config_free(line_cfg);
    if (in_settings)  gpiod_line_settings_free(in_settings);
    if (out_settings) gpiod_line_settings_free(out_settings);
    if (chip)         gpiod_chip_close(chip);
}

/* ─────────────────────────────────────────────────────────────────────────── */

int main(void)
{
    signal(SIGINT, handle_sigint);

    if (gpio_init() < 0)
        return EXIT_FAILURE;

    printf("Monitoring 74HC165 D6 — GPIO4(SH/LD) GPIO11(CLK) GPIO9(Q7)\n");
    printf("Press Ctrl+C to stop.\n\n");
    fflush(stdout);

    /* Set DEBUG_RAW to 1 to print every raw byte — useful for wiring checks */
#define DEBUG_RAW 1

    int prev_d6 = 0;
    unsigned long event_count = 0;
    uint8_t prev_byte = 0xFF;   /* force first debug print */

    while (running) {
        uint8_t byte = hc165_read_byte();
        int d6 = (byte & D6_MASK) ? 1 : 0;

#if DEBUG_RAW
        /* Print whenever the byte changes so the terminal isn't flooded */
        if (byte != prev_byte) {
            printf("[RAW] 0x%02X  "
                   "D7=%d D6=%d D5=%d D4=%d D3=%d D2=%d D1=%d D0=%d\n",
                   byte,
                   (byte >> 7) & 1, (byte >> 6) & 1,
                   (byte >> 5) & 1, (byte >> 4) & 1,
                   (byte >> 3) & 1, (byte >> 2) & 1,
                   (byte >> 1) & 1, (byte >> 0) & 1);
            fflush(stdout);
            prev_byte = byte;
        }
#endif

        /* Detect LOW → HIGH transition on D6 */
        if (d6 && !prev_d6) {
            struct timespec ts;
            clock_gettime(CLOCK_MONOTONIC, &ts);

            printf("[%8ld.%06ld]  D6 HIGH  (byte = 0x%02X)  event #%lu\n",
                   (long)ts.tv_sec,
                   ts.tv_nsec / 1000L,
                   byte,
                   ++event_count);
            fflush(stdout);
        }

        prev_d6 = d6;
        delay_us(POLL_INTERVAL_US);
    }

    printf("\nCaught SIGINT — %lu D6 rising-edge events recorded. Exiting.\n",
           event_count);

    gpio_cleanup();
    return EXIT_SUCCESS;
}
