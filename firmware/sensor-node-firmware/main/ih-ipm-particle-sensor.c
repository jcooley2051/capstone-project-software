#include "uart.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "ih-ipm-particle-sensor.h"


void get_particle_count(uint16_t *reading)
{
    int8_t read_data_cmd[] = {0xFE, 0xA5, 0x00, 0x00, 0xA5};
    uint8_t read_buffer[7];  // 7 bytes: Header + PM2.5 (2 bytes) + Checksum

    // Take the semaphore that protects the UART bus
    if (xSemaphoreTake(uart_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("get_particle_count", "Failed to take adxl i2c mutex");
        abort();
    }

    // Send read data command
    int bytes_sent = 0;
    int retry_count = 0;
    do
    {
        bytes_sent = uart_write_bytes(UART_PORT, (const char *)read_data_cmd, sizeof(read_data_cmd));
        retry_count++;
        if (bytes_sent != 5)
        {
            vTaskDelay(UART_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (bytes_sent != 5 && retry_count < UART_TRANSACTION_RETRY_COUNT);

    if (bytes_sent != 5)
    {
        ESP_LOGE("get_particle_count", "Error: Unexpected number of bytes sent");
    }

    // Wait for the response (12 bytes expected), allow up to 100 ms
    int length = uart_read_bytes(UART_PORT, read_buffer, sizeof(read_buffer), 100 / portTICK_PERIOD_MS);
    if (length == 7)
    {
        // This shouldn't overflow I don't think
        uint16_t checksum = 0xA5 + read_buffer[2] + read_buffer[3] + read_buffer[4] * 256 + read_buffer[5];
        // Validate response header and length
        if (read_buffer[0] == 0xFE && read_buffer[1] == 0xA5 && read_buffer[2] == 0x02 && read_buffer[6] == (checksum & 0x00FF))
        {
            *reading = read_buffer[4] * 256 + read_buffer[5];
        }
        else
        {
            ESP_LOGE("get_particle_count", "Invalid response structure");
            *reading = DUMMY_PARTICLE_COUNT;
        }
    }
    else
    {
        ESP_LOGE("get_particle_count", "Error: Unexpected number of bytes received");
        *reading = DUMMY_PARTICLE_COUNT;
    }
    xSemaphoreGive(uart_mutex);
}
