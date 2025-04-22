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
    uint8_t write_buffer[2];
    
    // Take control of the i2c bus
    if (xSemaphoreTake(adxl_i2c_mutex, TRANSMISSION_TIMEOUT_MS / portTICK_PERIOD_MS) != pdTRUE)
    {
        ESP_LOGE("configure_adxl", "Failed to take adxl i2c mutex");
        abort();
    }

    esp_err_t ret = ESP_OK;
    write_buffer[0] = ADXL_POWER_CRL_REGISTER;
    write_buffer[1] = 0x00; // Standby off
    ret = i2c_transmit_sensor(adxl_handle, write_buffer, sizeof(write_buffer));
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adxl", "Failed configuring setup time and filter for BME280");
        adxl_config_error = true;
    }


    write_buffer[0] = ADXL_FILTER_REGISTER;
    write_buffer[1] = 0x00; // No filtering, we do this on the Raspberry Pi
    ret = i2c_transmit_sensor(adxl_handle, write_buffer, sizeof(write_buffer));   
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adxl", "Failed configuring setup time and filter for BME280");
        adxl_config_error = true;
    }

    write_buffer[0] = ADXL_RANGE_REGISTER;
    write_buffer[1] = 0x03; // 8g
    ret = i2c_transmit_sensor(adxl_handle, write_buffer, sizeof(write_buffer));
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
    if (xSemaphoreTake(adxl_i2c_mutex, TRANSMISSION_TIMEOUT_MS / portTICK_PERIOD_MS) != pdTRUE)
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
        // Each reading takes up 9 bytes in teh buffer, starting in the first open byte
        ret = i2c_master_transmit_receive(adxl_handle, write_buffer, 1, &readings[i], 9, 5);
        vTaskDelayUntil(&last_wake_time, period_ticks);
        i += 9;
        count++;
    }

    // If Something went wrong, return dummy readings
    if (adxl_config_error || ret != ESP_OK)
    {
        ESP_LOGE("get_vibration_readings", "Failed to take reading, using dummy values");
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

/*
 Helper method used to convery the vibration readings into a large HEX string
*/
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