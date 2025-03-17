#include "config.h"
#include "i2c.h"
#include "esp_log.h"
#include "bme280-temp-sensor.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"


// Compensation factors to be read from Sensor
uint16_t dig_T1;
int16_t dig_T2;
int16_t dig_T3;
char dig_H1;
int16_t dig_H2;
char dig_H3;
int16_t dig_H4;
int16_t dig_H5;
char dig_H6;

static bool bme280_config_error = false;

// Configures the proper settings for our temperature and humidity readings
void configure_bme280(void)
{
    esp_err_t ret = ESP_OK;
    int retry_count = 0;

    // Holds bytes for writing
    uint8_t write_buffer[2];

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("configure_bme280", "Failed to take i2c mutex");
        abort();
    }

    // Configure standby time and filter
    write_buffer[0] = BME_CONFIG_REGISTER;
    write_buffer[1] = 0xD0; // 20ms stby time filter off (0b11100000)
    do
    {
        ret = i2c_master_transmit(bme_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    retry_count = 0;
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_bme280", "Failed configuring setup time and filter for BME280");
        bme280_config_error = true;
    }

    // Configure Temperature sampling and mode
    write_buffer[0] = BME_CTRL_MEAS_REGISTER;
    write_buffer[1] = 0xA3; // 16x oversampling, normal mode (0b10100011)
    do
    {
        ret = i2c_master_transmit(bme_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    retry_count = 0;
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_bme280", "Failed configuring temperature oversampling and mode for BME280");
        bme280_config_error = true;
    }

    // Configure Humidity Oversampling
    write_buffer[0] = BME_CTRL_HUM_REGISTER;
    write_buffer[1] = 0x05; // 16x oversampling (0b00000101)
    do
    {
        ret = i2c_master_transmit(bme_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_bme280", "Failed configureing humidity oversampling for BME280");
        bme280_config_error = true;
    }

    // Release the bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("configure_bme280", "Failed to give i2c mutex");
        abort();
    }
}

// Reads compensation values from registers on the BME280
void read_compensation_bme280(void)
{
    uint8_t write_buffer[1];
    uint8_t read_buffer[2];

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to take i2c mutex");
        abort();
    }

    // Read dig_T1
    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    write_buffer[0] = DIG_T1_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_T1 from BME280");
        bme280_config_error = true;
    }

    dig_T1 = (read_buffer[1] << 8) | read_buffer[0];

    // Read dig_T2
    retry_count = 0;
    write_buffer[0] = DIG_T2_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_T2 from BME280");
        bme280_config_error = true;
    }

    dig_T2 = (read_buffer[1] << 8) | read_buffer[0];

    // Read dig_T3
    retry_count = 0;
    write_buffer[0] = DIG_T3_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_T3 from BME280");
        bme280_config_error = true;
    }

    dig_T3 = (read_buffer[1] << 8) | read_buffer[0];  

    // Read dig_H1
    retry_count = 0;
    write_buffer[0] = DIG_H1_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_H1 from BME280");
        bme280_config_error = true;
    }

    dig_H1 = read_buffer[0];

    // Read dig_H2
    retry_count = 0;
    write_buffer[0] = DIG_H2_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_H2 from BME280");
        bme280_config_error = true;
    }

    dig_H2 = (read_buffer[1] << 8) | read_buffer[0];

    // Read dig_H3
    retry_count = 0;
    write_buffer[0] = DIG_H3_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_H3 from BME280");
        bme280_config_error = true;
    }

    dig_H3 = read_buffer[0];

    // Read dig_H4
    retry_count = 0;
    write_buffer[0] = DIG_H4_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_H4 from BME280");
        bme280_config_error = true;
    }

    dig_H4 = (read_buffer[0] << 4) | (read_buffer[1] & 0xF);

    // Read dig_H5
    retry_count = 0;
    write_buffer[0] = DIG_H5_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_H5 from BME280");
        bme280_config_error = true;
    }

    dig_H5 = (read_buffer[1] << 4) | ((read_buffer[0] & 0xF0) >> 4);

    // Read dig_H6
    retry_count = 0;
    write_buffer[0] = DIG_H6_REGISTER;
    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            retry_count++;
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);
    
    if (ret != ESP_OK)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to read dig_H6 from BME280");
        bme280_config_error = true;
    }

    dig_H6 = read_buffer[0];

    // Release bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to give i2c mutex");
        abort();
    }
}

// Function to get temperature and humidity readings from the BME280, they need to be together because temperature is used in calculating the RH
void get_temp_and_humidity(temp_and_humidity_t *readings)
{
    int retry_count = 0;
    esp_err_t ret = ESP_OK;

    // Starting address for temperature and humidity readings
    uint8_t write_buffer[1] = {BME_READINGS_REGISTER};
    uint8_t read_buffer[8]; 

    // Take ownership of I2C bus
    if (xSemaphoreTake(i2c_mutex, portMAX_DELAY) != pdTRUE)
    {
        ESP_LOGE("get_temp_and_humidity", "Failed to take i2c mutex");
        abort();
    }

    do
    {
        ret = i2c_master_transmit_receive(bme_handle, write_buffer, 1, read_buffer, 8, portMAX_DELAY);
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_TRANSMISSION_RETRY_DELAY / portTICK_PERIOD_MS);
            retry_count++;
        }
    } while(ret != ESP_OK && retry_count < I2C_TRANSACTION_RETRY_COUNT);

    // Release bus
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("read_compensation_bme280", "Failed to give i2c mutex");
        abort();
    }

    // If there is a failure in the reading, set a dummy value of (-500C, 150% humidity to be detected by analysis software)
    if (bme280_config_error == true || ret != ESP_OK) {
        readings->temp_reading = DUMMY_TEMP_READING;
        readings->humidity_reading = DUMMY_HUMIDITY_READING;
        return;
    }

    int32_t t_fine; // Fine temperature to use in humidity calculation

    // Print temperature readings (for explaination, visit BME280 datasheet)
    int32_t temp_reading = (read_buffer[3] << 12) | (read_buffer[4] << 4) | ((read_buffer[5] & 0xF0) >> 4);
    int32_t var1, var2;
    var1 = ((((temp_reading >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
    var2 = (((((temp_reading >> 4) - ((int32_t)dig_T1)) * ((temp_reading >> 4) - ((int32_t)dig_T1))) >> 12) * ((int32_t)dig_T3)) >> 14;
    t_fine = var1 + var2;
    // resolution is 0.01 DegC, so "1234" equals 12.34 DegC
    readings->temp_reading = (t_fine * 5 + 128) >> 8;

    // Print humidity readings (for explaination, visit BME280 datasheet)
    int32_t humidity_reading = (read_buffer[6] << 8) | read_buffer[7];
    int32_t v_x1_u32r;
    v_x1_u32r = (t_fine - ((int32_t)76800));
    v_x1_u32r = (((((humidity_reading << 14) - (((int32_t)dig_H4) << 20) - (((int32_t)dig_H5) * v_x1_u32r)) + ((int32_t)16384)) >> 15) * 
                (((((((v_x1_u32r * ((int32_t)dig_H6)) >> 10) * (((v_x1_u32r * ((int32_t)dig_H3)) >> 11) + ((int32_t)32768))) >> 10) + 
                ((int32_t)2097152)) * ((int32_t)dig_H2) + 8192) >> 14));
    v_x1_u32r = (v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * ((int32_t)dig_H1)) >> 4));
    v_x1_u32r = (v_x1_u32r < 0 ? 0 : v_x1_u32r);
    v_x1_u32r = (v_x1_u32r > 419430400 ? 419430400 : v_x1_u32r);
    // Percent RH as unsigned 32 bit integer in Q22.10 format
    readings->humidity_reading = (uint32_t)(v_x1_u32r >> 12);
}

