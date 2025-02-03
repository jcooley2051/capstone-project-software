#ifndef UART_H
#define UART_H

#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define UART_CONSOLE_TAG "UART"

// Transmit and receive pins for UART
#define RX_GPIO_PIN 16
#define TX_GPIO_PIN 17

// Uart port number to use
#define UART_PORT UART_NUM_1

// Buffer size for the UART peripheral
#define UART_BUF_SIZE 256

// The particle count sensor works at a 1200 baud rate
#define UART_BAUD_RATE 1200

//Retry any failed transaction up to I2C_TRANSACTION_RETRY_COUNT times
#define UART_TRANSACTION_RETRY_COUNT 3
// 50 ms delay between transmissions if failure
#define UART_TRANSMISSION_RETRY_DELAY 50

//Retry any failed transaction up to I2C_SETUP_RETRY_COUNT times
#define UART_SETUP_RETRY_COUNT 3
// 100 ms delay between setup calls if failure
#define UART_SETUP_RETRY_DELAY 100

// Mutex to protect the UART
extern SemaphoreHandle_t uart_mutex;

/* Initialize the UART peripheral for communication with the particle count sensor */
void init_uart(void);


#endif