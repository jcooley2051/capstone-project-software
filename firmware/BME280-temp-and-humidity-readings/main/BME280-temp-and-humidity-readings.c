#include <stdio.h>
#include "esp_log.h"
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "BME280-temp-and-humidity-readings.h"

#define I2C_CONSOLE_TAG "I2C"
#define SYSTEM_CONSOLE_TAG "System"
#define BME_CONSOLE_TAG "BME280"

#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5
#define I2C_PORT_AUTO -1
#define SENSOR_ADDRESS 0x77

// Compensation factors from Sensor
uint16_t dig_T1;
int16_t dig_T2;
int16_t dig_T3;
uint8_t dig_H1;
int16_t dig_H2;
uint8_t dig_H3;
int16_t dig_H4;
int16_t dig_H5;
int8_t dig_H6;

// I2C handles
i2c_master_bus_handle_t bus_handle;
i2c_master_dev_handle_t dev_handle;

void init_i2c(void)
{
    i2c_master_bus_config_t i2c_mst_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_PORT_AUTO,
        .scl_io_num = SCL_GPIO_PIN,
        .sda_io_num = SDA_GPIO_PIN,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };  

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = SENSOR_ADDRESS,
        .scl_speed_hz = 100000,
    };

    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle));
}

void configure_bme280(void)
{
    // Holds bytes for writing
    uint8_t write_buffer[2];

    // Configure standby time (20ms) and filter (Off) 0b11100000
    write_buffer[0] = 0xF5; // Register Address
    write_buffer[1] = 0xD0;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Configure Temperature Oversampling (16x) and mode (Normal) 0b10100011
    write_buffer[0] = 0xF4; // Register Address
    write_buffer[1] = 0xA3;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Configure Humidity Oversampling (16x) 0b00000101
    write_buffer[0] = 0xF2; // Register Address
    write_buffer[1] = 0x05;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));
}

void read_compensation(void)
{
    uint8_t write_buffer[1];
    uint8_t read_buffer[2];

    // Read dig_T1
    write_buffer[0] = 0x88;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T1 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_T1);

    // Read dig_T2
    write_buffer[0] = 0x8A;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T2 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_T2);

    // Read dig_T3
    write_buffer[0] = 0x8C;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T3 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_T3);     

    // Read dig_H1
    write_buffer[0] = 0xA1;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H1 = read_buffer[0];
    printf("%d\n", dig_H1);

    // Read dig_H2
    write_buffer[0] = 0xE1;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H2 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_H2);

    // Read dig_H3
    write_buffer[0] = 0xE3;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H3 = read_buffer[0];
    printf("%d\n", dig_H3);

    // Read dig_H4
    write_buffer[0] = 0xE4;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H4 = (read_buffer[0] << 4) | (read_buffer[1] & 0xF);
    printf("%d\n", dig_H4);

    // Read dig_H5
    write_buffer[0] = 0xE5;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H5 = (read_buffer[1] << 4) | (read_buffer[0] & 0xF0 >> 4);
    printf("%d\n", dig_H5);

    // Read dig_H6
    write_buffer[0] = 0xE7;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H6 = read_buffer[0];
    printf("%d\n", dig_H6);    
}

void bme_readings_task(void *arg)
{
    ESP_LOGI("Debug", "BME readings task");
    vTaskDelay(100);
    uint8_t write_buffer[1] = {0xF7};
    uint8_t read_buffer[8];
    while(1)
    {
        ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, 1, read_buffer, 8, portMAX_DELAY));
        print_sensor_readings(read_buffer);
        vTaskDelay(250 / portTICK_PERIOD_MS);  // 250ms delay
    }
}

void print_sensor_readings(uint8_t *readings)
{
    int32_t t_fine; // Fine temperature to use in humidity calculation

    // Print temperature readings (for explaination, visit BME280 datasheet)
    int32_t temp_reading = (readings[3] << 12) | (readings[4] << 4) | ((readings[5] & 0xF0) >> 4);
    int32_t var1, var2, temp;
    var1 = ((((temp_reading >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
    var2 = (((((temp_reading >> 4) - ((int32_t)dig_T1)) * ((temp_reading >> 4) - ((int32_t)dig_T1))) >> 12) * ((int32_t)dig_T3)) >> 14;
    t_fine = var1 + var2;
    // resolution is 0.01 DegC, so "1234" equals 12.34 DegC
    temp = (t_fine * 5 + 128) >> 8;
    printf("Temp: %0.2f C\n", temp/100.0);

    // Print humidity readings (for explaination, visit BME280 datasheet)
    int32_t humidity_reading = (readings[6] << 8) | readings[7];
    int32_t v_x1_u32r;
    uint32_t humidity;
    v_x1_u32r = (t_fine - ((int32_t)76800));
    v_x1_u32r = (((((humidity_reading << 14) - (((int32_t)dig_H4) << 20) - (((int32_t)dig_H5) * v_x1_u32r)) + ((int32_t)16384)) >> 15) * 
                (((((((v_x1_u32r * ((int32_t)dig_H6)) >> 10) * (((v_x1_u32r * ((int32_t)dig_H3)) >> 11) + ((int32_t)32768))) >> 10) + 
                ((int32_t)2097152)) * ((int32_t)dig_H2) + 8192) >> 14));
    v_x1_u32r = (v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * ((int32_t)dig_H1)) >> 4));
    v_x1_u32r = (v_x1_u32r < 0 ? 0 : v_x1_u32r);
    v_x1_u32r = (v_x1_u32r > 419430400 ? 419430400 : v_x1_u32r);
    // Percent RH as unsigned 32 bit integer in Q22.10 format
    humidity = (uint32_t)(v_x1_u32r >> 12);
    printf("Humidity: %0.2f %%\n", humidity/1024.0);
}

void app_main(void)
{
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting System");

    // Initialize the I2C driver to work with the 
    ESP_LOGI(I2C_CONSOLE_TAG, "Initializing I2C");
    init_i2c();
    ESP_LOGI(I2C_CONSOLE_TAG, "Successfullty Initialized I2C");

    ESP_LOGI(BME_CONSOLE_TAG, "Configuring BME280");
    configure_bme280();
    ESP_LOGI(BME_CONSOLE_TAG, "Successfully Configured BME280");

    ESP_LOGI(BME_CONSOLE_TAG, "Reading Compensation Values");
    read_compensation();
    ESP_LOGI(BME_CONSOLE_TAG, "Successfully Read Compensation");

    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting Readings Task");
    xTaskCreate(bme_readings_task, "Temp/Humidity Readings Task", 2048, NULL, 5, NULL);
}
