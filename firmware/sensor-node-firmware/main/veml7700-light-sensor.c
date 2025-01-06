#include "veml7700-light-sensor.h"
#include "i2c.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

void configure_veml7700(void)
{
    uint8_t write_buffer[3];
    write_buffer[0] = 0x00;
    write_buffer[1] = 0x00;
    write_buffer[2] = 0x00;

    // Take ownership of I2C bus
    xSemaphoreTake(i2c_mutex, portMAX_DELAY);

    ESP_ERROR_CHECK(i2c_master_transmit(veml_handle, write_buffer, 3, portMAX_DELAY));
    
    // Release bus
    xSemaphoreGive(i2c_mutex);
}

void get_light_level(light_readings_t *readings)
{
    uint8_t write_buffer[1] = {0x04};
    uint8_t als_read_buffer[2];
    uint8_t white_read_buffer[2];

    // Take ownership of I2C bus
    xSemaphoreTake(i2c_mutex, portMAX_DELAY);

    ESP_ERROR_CHECK(i2c_master_transmit_receive(veml_handle, write_buffer, 1, als_read_buffer, 2, portMAX_DELAY));
    write_buffer[0] = 0x05;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(veml_handle, write_buffer, 1, white_read_buffer, 2, portMAX_DELAY));

    // Release bus
    xSemaphoreGive(i2c_mutex);

    uint16_t reading = (als_read_buffer[1] << 8) | als_read_buffer[0];
    readings->als_reading = reading * RESOLUTION;
    
    //TODO: Remove after testing
    //printf("ALS light Level: %0.2f lux\n", readings->als_reading);
    reading = (white_read_buffer[1] << 8) | white_read_buffer[0];
    readings->white_reading = reading * RESOLUTION;

    //TODO: Remove after testing
    //printf("White light Level: %0.2f lux\n", readings->white_reading);
}