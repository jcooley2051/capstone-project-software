#include "i2c.h"
#include "bme280-temp-sensor.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"


// Compensation factors to be read from Sensor
uint16_t dig_T1;
int16_t dig_T2;
int16_t dig_T3;
uint8_t dig_H1;
int16_t dig_H2;
uint8_t dig_H3;
int16_t dig_H4;
int16_t dig_H5;
int8_t dig_H6;

// Configures the proper settings for our temperature and humidity readings
void configure_bme280(void)
{
    // Holds bytes for writing
    uint8_t write_buffer[2];

    // Take ownership of I2C bus
    xSemaphoreTake(i2c_mutex, portMAX_DELAY);

    // Configure standby time (20ms) and filter (Off) 0b11100000
    write_buffer[0] = 0xF5; // Register Address
    write_buffer[1] = 0xD0;
    ESP_ERROR_CHECK(i2c_master_transmit(bme_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Configure Temperature Oversampling (16x) and mode (Normal) 0b10100011
    write_buffer[0] = 0xF4; // Register Address
    write_buffer[1] = 0xA3;
    ESP_ERROR_CHECK(i2c_master_transmit(bme_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Configure Humidity Oversampling (16x) 0b00000101
    write_buffer[0] = 0xF2; // Register Address
    write_buffer[1] = 0x05;
    ESP_ERROR_CHECK(i2c_master_transmit(bme_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Release bus
    xSemaphoreGive(i2c_mutex);
}

// Reads compensation values from registers on the BME280
void read_compensation_bme280(void)
{
    uint8_t write_buffer[1];
    uint8_t read_buffer[2];

    // Take ownership of I2C bus
    xSemaphoreTake(i2c_mutex, portMAX_DELAY);

    // Read dig_T1
    write_buffer[0] = 0x88;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T1 = (read_buffer[1] << 8) | read_buffer[0];

    // Read dig_T2
    write_buffer[0] = 0x8A;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T2 = (read_buffer[1] << 8) | read_buffer[0];

    // Read dig_T3
    write_buffer[0] = 0x8C;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T3 = (read_buffer[1] << 8) | read_buffer[0];  

    // Read dig_H1
    write_buffer[0] = 0xA1;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H1 = read_buffer[0];

    // Read dig_H2
    write_buffer[0] = 0xE1;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H2 = (read_buffer[1] << 8) | read_buffer[0];

    // Read dig_H3
    write_buffer[0] = 0xE3;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H3 = read_buffer[0];

    // Read dig_H4
    write_buffer[0] = 0xE4;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H4 = (read_buffer[0] << 4) | (read_buffer[1] & 0xF);

    // Read dig_H5
    write_buffer[0] = 0xE5;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H5 = (read_buffer[1] << 4) | (read_buffer[0] & 0xF0 >> 4);

    // Read dig_H6
    write_buffer[0] = 0xE7;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H6 = read_buffer[0];

    // Release bus
    xSemaphoreGive(i2c_mutex);
}

// Function to get temperature and humidity readings from the BME280, they need to be together because temperature is used in calculating the RH
void get_temp_and_humidity(temp_and_humidity_t *results)
{
    // Starting address for temperature and humidity readings
    uint8_t write_buffer[1] = {0xF7};
    uint8_t read_buffer[8]; 

    // Take ownership of I2C bus
    xSemaphoreTake(i2c_mutex, portMAX_DELAY);

    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_handle, write_buffer, 1, read_buffer, 8, portMAX_DELAY));

    // Release bus
    xSemaphoreGive(i2c_mutex);

    int32_t t_fine; // Fine temperature to use in humidity calculation

    // Print temperature readings (for explaination, visit BME280 datasheet)
    int32_t temp_reading = (read_buffer[3] << 12) | (read_buffer[4] << 4) | (read_buffer[5] & 0xF0 >> 4);
    int32_t var1, var2;
    var1 = ((((temp_reading >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
    var2 = (((((temp_reading >> 4) - ((int32_t)dig_T1)) * ((temp_reading >> 4) - ((int32_t)dig_T1))) >> 12) * ((int32_t)dig_T3)) >> 14;
    t_fine = var1 + var2;
    // resolution is 0.01 DegC, so "1234" equals 12.34 DegC
    results->temp_reading = (t_fine * 5 + 128) >> 8;

    //TODO: remove after testing
    printf("Temp: %0.2f C\n", results->temp_reading/100.0);

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
    results->humidity_reading = (uint32_t)(v_x1_u32r >> 12);

    //TODO: remove after testing
    printf("Humidity: %0.2f %%\n", results->humidity_reading/1024.0);
}

