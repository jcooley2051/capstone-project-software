#include "config.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "include/uart.h"


#ifdef SPIN_COATING
// Mutex for resource protection
SemaphoreHandle_t uart_mutex;


// UART configuration
void init_uart(void)
{
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };
    
    int retry_count = 0;
    esp_err_t ret = ESP_OK;

    // Install UART driver
    do
    {
        ret = uart_driver_install(UART_PORT, UART_BUF_SIZE, 0, 0, NULL, 0);
        retry_count++;
            if (ret != ESP_OK)
        {
            vTaskDelay(UART_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < UART_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("init_uart", "Failed to install UART driver");
        abort();
    }

    // Configure UART peripheral
    retry_count = 0;
    do
    {
        ret = uart_param_config(UART_PORT, &uart_config);
        retry_count++;
            if (ret != ESP_OK)
        {
            vTaskDelay(UART_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < UART_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("init_uart", "Failed to configure UART");
        abort();
    }

    // Set UART pins
    retry_count = 0;
    do
    {
        ret = uart_set_pin(UART_PORT, TX_GPIO_PIN, RX_GPIO_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
        retry_count++;
            if (ret != ESP_OK)
        {
            vTaskDelay(UART_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < UART_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("init_uart", "Failed to set UART pins");
        abort();
    }

    // Set the drive capability for the GPIO pins (may be removed)
    gpio_set_drive_capability(TX_GPIO_PIN, GPIO_DRIVE_CAP_3);
    gpio_set_drive_capability(RX_GPIO_PIN, GPIO_DRIVE_CAP_3);

    // Create the binary semaphore for the I2C mutex
    do
    {
        uart_mutex = xSemaphoreCreateBinary();
        retry_count++;
        if (uart_mutex == NULL)
        {
            vTaskDelay(UART_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(uart_mutex == NULL && retry_count < UART_SETUP_RETRY_COUNT);

    if (uart_mutex == NULL)
    {
        ESP_LOGE("init_uart", "Failed to initialize UART mutex. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }

    
    // Binary semaphores are zero by default, there is no risk of failure in this action
    xSemaphoreGive(uart_mutex);
}
#endif