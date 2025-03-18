#include "config.h"
#include "i2c.h"
#include "adxl-vibration-sensor.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)

static bool adxl_config_error = false;


void configure_adxl(void)
{
    // Take control of the i2c bus
    if (xSemaphoreTake(adxl_i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("configure_adxl", "Failed to take adxl i2c mutex");
        abort();
    }
    esp_err_t ret = ESP_OK;

    uint8_t write_buffer[2];
    write_buffer[0] = ADXL_POWER_CRL_REGISTER;
    write_buffer[1] = 0x00; // Standby off
    int retry_count = 0;
    do
    {
        ret = i2c_master_transmit(adxl_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adxl", "Failed configuring setup time and filter for BME280");
        adxl_config_error = true;
    }


    write_buffer[0] = ADXL_FILTER_REGISTER;
    write_buffer[1] = 0x00;
    retry_count = 0;
    do
    {
        ret = i2c_master_transmit(adxl_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adxl", "Failed configuring setup time and filter for BME280");
        adxl_config_error = true;
    }

    write_buffer[0] = ADXL_RANGE_REGISTER;
    write_buffer[1] = 0x01; // 2g
    retry_count = 0;
    do
    {
        ret = i2c_master_transmit(adxl_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adxl", "Failed configuring setup time and filter for BME280");
        adxl_config_error = true;
    }

    // Release the i2c bus
    if (xSemaphoreGive(adxl_i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("configure_adxl", "Failed to give adxl i2c mutex");
        abort();
    }
}


void get_vibration_readings(uint8_t *readings)
{
    // Take the i2c bus
    if (xSemaphoreTake(adxl_i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("get_vibration_readings", "Failed to take adxl i2c mutex");
        abort();
    }
    // Address of the registers to start reading acceleration data at
    uint8_t write_buffer[1] = {ADXL_READINGS_REGISTER};
    const TickType_t period_ticks = pdMS_TO_TICKS(1000 / ADXL_SAMPLE_RATE);
    int count = 0;
    int i = 0;
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
    if (adxl_config_error || ret != ESP_OK)
    {
        for(int i = 0; i < ADXL_NUM_READINGS*ADXL_READING_SIZE_BYTES; i++)
        {
            readings[i] = ADXL_DUMMY_VALUE;
        }
    }

    // Release the i2c bus
    if (xSemaphoreGive(adxl_i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("configure_adxl", "Failed to give adxl i2c mutex");
        abort();
    }
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
#endif