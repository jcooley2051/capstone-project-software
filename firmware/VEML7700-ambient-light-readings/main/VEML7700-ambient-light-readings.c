#include <stdio.h>
#include "esp_log.h"
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "VEML7700-ambient-light-readings.h"

#define I2C_CONSOLE_TAG "I2C"
#define SYSTEM_CONSOLE_TAG "System"
#define VEML_CONSOLE_TAG "VEML7700"

#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5
#define I2C_PORT_AUTO -1
#define SENSOR_ADDRESS 0x10

//#define RESOLUTION 0.0168f
#define RESOLUTION 0.0336f

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
        .scl_speed_hz = 400000,
    };

    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle));
}

void configure_veml7700(void)
{
    uint8_t write_buffer[3];
    write_buffer[0] = 0x00;
    write_buffer[1] = 0x10;
    write_buffer[2] = 0x00;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 3, portMAX_DELAY));
    // Placeholder in case we decide to customize configuration
}

void veml_readings_task(void *arg)
{
    uint8_t write_buffer[1] = {0x04};
    uint8_t als_read_buffer[2];
    uint8_t white_read_buffer[2];
    
    while(1)
    {
        ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, 1, als_read_buffer, 2, portMAX_DELAY));
        write_buffer[0] = 0x05;
        ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, 1, white_read_buffer, 2, portMAX_DELAY));
        print_sensor_reading(als_read_buffer, white_read_buffer);
        vTaskDelay(750 / portTICK_PERIOD_MS);  // 750ms delay (600ms refresh rate MAX)
    }
}

void print_sensor_reading(uint8_t *als_light_reading, uint8_t *white_light_reading)
{
    uint16_t reading = (als_light_reading[1] << 8) | als_light_reading[0];
    float lux_level = reading * RESOLUTION;
    printf("ALS light Level: %0.2f lux\n", lux_level);
    reading = (white_light_reading[1] << 8) | white_light_reading[0];
    lux_level = reading * RESOLUTION;
    printf("White light Level: %0.2f lux\n", lux_level);
}

void app_main(void)
{
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting System");

    // Initialize the I2C driver to work with the 
    ESP_LOGI(I2C_CONSOLE_TAG, "Initializing I2C");
    init_i2c();
    ESP_LOGI(I2C_CONSOLE_TAG, "Successfullty Initialized I2C");

    // Configure VEML7700 ambient light sensor
    ESP_LOGI(VEML_CONSOLE_TAG, "Configuring VEML7700");
    configure_veml7700();
    ESP_LOGI(VEML_CONSOLE_TAG, "Successfully Configured VEML7700");

    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting Readings Task");
    xTaskCreate(veml_readings_task, "Temp/Humidity Readings Task", 2048, NULL, 5, NULL);
}
