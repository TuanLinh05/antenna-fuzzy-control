#include "uart_link.h"

#include <string.h>
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/ring_buffer.h>

#include "link_proto.h"

static const struct device *const uart = DEVICE_DT_GET(DT_NODELABEL(usart1));

RING_BUF_DECLARE(tx_ring, CONFIG_ANTENNA_TX_BUF_SIZE);
K_MSGQ_DEFINE(rx_lines, LINK_LINE_MAX, 8, 4);

static char rx_buf[LINK_LINE_MAX];
static size_t rx_len;
static bool rx_overflow;
static uint32_t dropped;

static void uart_isr(const struct device *dev, void *user_data)
{
	ARG_UNUSED(user_data);
	while (uart_irq_update(dev) && uart_irq_is_pending(dev)) {
		if (uart_irq_rx_ready(dev)) {
			uint8_t buf[16];
			int n = uart_fifo_read(dev, buf, sizeof(buf));

			for (int i = 0; i < n; i++) {
				char c = (char)buf[i];

				if (c == '\r') {
					continue;
				}
				if (c == '\n') {
					if (!rx_overflow && rx_len > 0u) {
						rx_buf[rx_len] = 0;
						(void)k_msgq_put(&rx_lines, rx_buf, K_NO_WAIT);
					}
					rx_len = 0u;
					rx_overflow = false;
				} else if (rx_len < sizeof(rx_buf) - 1u) {
					rx_buf[rx_len++] = c;
				} else {
					rx_overflow = true; /* line too long: dropped */
				}
			}
		}
		if (uart_irq_tx_ready(dev)) {
			uint8_t *data;
			uint32_t n = ring_buf_get_claim(&tx_ring, &data, 16u);

			if (n == 0u) {
				ring_buf_get_finish(&tx_ring, 0u);
				uart_irq_tx_disable(dev);
			} else {
				int sent = uart_fifo_fill(dev, data, (int)n);

				ring_buf_get_finish(&tx_ring, sent > 0 ? (uint32_t)sent : 0u);
			}
		}
	}
}

int uart_link_init(void)
{
	if (!device_is_ready(uart)) {
		return -ENODEV;
	}
	uart_irq_callback_user_data_set(uart, uart_isr, NULL);
	uart_irq_rx_enable(uart);
	return 0;
}

int uart_link_get_line(char *buf, size_t size)
{
	char line[LINK_LINE_MAX];

	if (k_msgq_get(&rx_lines, line, K_NO_WAIT) != 0) {
		return -EAGAIN;
	}
	strncpy(buf, line, size - 1u);
	buf[size - 1u] = 0;
	return 0;
}

size_t uart_link_write(const char *text)
{
	size_t len = strlen(text);
	unsigned int key = irq_lock();
	uint32_t put;

	if (ring_buf_space_get(&tx_ring) < len) {
		put = 0u; /* never send a partial line */
	} else {
		put = ring_buf_put(&tx_ring, (const uint8_t *)text, (uint32_t)len);
	}
	irq_unlock(key);
	if (put != len) {
		dropped += (uint32_t)(len - put);
	}
	uart_irq_tx_enable(uart);
	return len - put;
}

uint32_t uart_link_dropped(void)
{
	return dropped;
}
