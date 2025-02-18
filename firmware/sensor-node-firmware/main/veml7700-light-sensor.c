#include "veml7700-light-sensor.h"
#include "i2c.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"


static bool veml7700_config_error = false;

void configure_veml7700(void)
{
    uint8_t write_buffer[3] = {0x00, 0x10, 0x00};

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("configure_veml7700", "Failed to take i2c mutex");
        abort();
    }

    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    do
    {
        ret = i2c_master_transmit(veml_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        if (ret != ESP_OK)
        {
            veml7700_config_error = true;
            retry_count++;
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    
    // Release bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("configure_veml7700", "Failed to give i2c mutex");
        abort();
    }
}

void get_light_level(light_readings_t *readings)
{
    uint8_t write_buffer[1] = {0x04};
    uint8_t als_read_buffer[2];
    uint8_t white_read_buffer[2];

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("get_light_level", "Failed to take i2c mutex");
        abort();
    }

    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    do
    {
        ret = i2c_master_transmit_receive(veml_handle, write_buffer, 1, als_read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret == ESP_OK)
    {
        write_buffer[0] = 0x05;
        retry_count = 0;
        ret = ESP_OK;
        do
        {
            ret = i2c_master_transmit_receive(veml_handle, write_buffer, 1, white_read_buffer, 2, portMAX_DELAY);
            if (ret != ESP_OK)
            {
                retry_count++;
                vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
            }
        } while(ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    }
    // Release bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("get_light_level", "Failed to give i2c mutex");
        abort();
    }

    if (ret != ESP_OK || veml7700_config_error)
    {
        readings->als_reading = DUMMY_LIGHT_READING;
        readings->white_reading = DUMMY_LIGHT_READING;
        return;
    }

    uint16_t reading = (als_read_buffer[1] << 8) | als_read_buffer[0];
    readings->als_reading = reading * RESOLUTION;
    
    //TODO: Remove after testing
    //printf("ALS light Level: %0.2f lux\n", readings->als_reading);
    reading = (white_read_buffer[1] << 8) | white_read_buffer[0];
    readings->white_reading = reading * RESOLUTION;

    //TODO: Remove after testing
    //printf("White light Level: %0.2f lux\n", readings->white_reading);
}