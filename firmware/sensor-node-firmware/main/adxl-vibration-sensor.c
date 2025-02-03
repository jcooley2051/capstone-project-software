#include "i2c.h"
#include "adxl-vibration-sensor.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"


void configure_adxl(void)
{
    uint8_t write_buffer[2];
    write_buffer[0] = 0x2D;
    write_buffer[1] = 0x92;
    ESP_ERROR_CHECK(i2c_master_transmit(adxl_handle, write_buffer, 2, portMAX_DELAY));

    write_buffer[0] = 0x28;
    write_buffer[1] = 0x01;
    ESP_ERROR_CHECK(i2c_master_transmit(adxl_handle, write_buffer, 2, portMAX_DELAY));

    write_buffer[0] = 0x2C;
    write_buffer[1] = 0x01;
    ESP_ERROR_CHECK(i2c_master_transmit(adxl_handle, write_buffer, 2, portMAX_DELAY));
    // Placeholder in case we decide to customize configuration
}


void get_vibration_readings(uint8_t *readings)
{
    // Address of the registers to start reading acceleration data at
    uint8_t write_buffer[1] = {0x08};
    const TickType_t period_ticks = pdMS_TO_TICKS(1000 / ADXL_SAMPLE_RATE);
    int count = 0;
    int i = 0;
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE(I2C_CONSOLE_TAG, "Failed to take adxl i2c mutex");
        abort();
    }
    TickType_t last_wake_time = xTaskGetTickCount();
    esp_err_t ret = ESP_OK;
    // Due to the strict timing requirements, we don't retry taking readings. 
    // We simply send dummy values if any of the readings fail
    while(count < ADXL_NUM_READINGS && ret == ESP_OK)
    {
        ret = i2c_master_transmit_receive(adxl_handle, write_buffer, 1, &readings[i], 9, portMAX_DELAY);
        vTaskDelayUntil(&last_wake_time, period_ticks);
        i += 9;
        count++;
    }
    if (ret != ESP_OK)
    {
        for(int i = 0; i < ADXL_NUM_READINGS*ADXL_READING_SIZE_BYTES; i++)
        {
            readings[i] = ADXL_DUMMY_VALUE;
        }
    }

    xSemaphoreGive(adxl_i2c_mutex);
}

void encode_to_hex(uint8_t *readings_buffer, size_t buffer_length, char *output_buffer)
{
    const char *hex_chars = "0123456789ABCDEF";
    for (size_t i = 0; i < buffer_length; ++i) {
        output_buffer[i * 2] = hex_chars[(readings_buffer[i] >> 4) & 0x0F];
        output_buffer[i * 2 + 1] = hex_chars[readings_buffer[i] & 0x0F];
    }
    output_buffer[buffer_length * 2] = '\0'; // Null-terminate the string
}