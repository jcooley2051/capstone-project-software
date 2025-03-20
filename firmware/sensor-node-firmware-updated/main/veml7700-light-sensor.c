#include "config.h"
#include "veml7700-light-sensor.h"
#include "i2c.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#if defined(PHOTOLITHOGRAPHY) || defined(SPUTTERING)

static bool veml7700_config_error = false;

void configure_veml7700(void)
{
    esp_err_t ret = ESP_OK;
    // Little Endian, 1x gain, 400ms integration time
    uint8_t write_buffer[3] = {VEML_CONFIG_REGISTER, 0x80, 0x00};

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("configure_veml7700", "Failed to take i2c mutex");
        abort();
    }

    ret = i2c_transmit_sensor(veml_handle, write_buffer, sizeof(write_buffer));
    
    // Release bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("configure_veml7700", "Failed to give i2c mutex");
        abort();
    }
}

void get_light_level(light_readings_t *readings)
{
    uint8_t write_buffer[1] = {VEML_ALS_READING_REGISTER};
    uint8_t als_read_buffer[2];
    uint8_t white_read_buffer[2];

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("get_light_level", "Failed to take i2c mutex");
        abort();
    }

    esp_err_t ret = ESP_OK;
    ret = i2c_transmit_receive_sensor(veml_handle, write_buffer, sizeof(write_buffer), als_read_buffer, sizeof(als_read_buffer));
    if (ret == ESP_OK)
    {
        write_buffer[0] = VEML_WHITE_READING_REGISTER;
        ret = i2c_transmit_receive_sensor(veml_handle, write_buffer, sizeof(write_buffer), white_read_buffer, sizeof(white_read_buffer));
    }

    // Release bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("get_light_level", "Failed to give i2c mutex");
        abort();
    }

    if (ret != ESP_OK || veml7700_config_error)
    {
        ESP_LOGE("get_light_level", "Failed to get light level, using dummy readings");
        readings->als_reading = DUMMY_LIGHT_READING;
        readings->white_reading = DUMMY_LIGHT_READING;
        return;
    }

    uint16_t reading = ((als_read_buffer[1] << 8) | als_read_buffer[0]);
    readings->als_reading = reading * RESOLUTION;
    
    reading = ((white_read_buffer[1] << 8) | white_read_buffer[0]);
    readings->white_reading = reading * RESOLUTION;
}
#endif