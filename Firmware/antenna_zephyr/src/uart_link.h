/* Interrupt-driven USART1: received lines -> queue, text -> TX ring buffer. */
#ifndef UART_LINK_H
#define UART_LINK_H

#include <stddef.h>
#include <stdint.h>

int uart_link_init(void);
/* Non-blocking: copies one received line (NUL-terminated) into buf. */
int uart_link_get_line(char *buf, size_t size);
/* Queues text for transmission; returns bytes dropped when the buffer is full. */
size_t uart_link_write(const char *text);
uint32_t uart_link_dropped(void);

#endif
