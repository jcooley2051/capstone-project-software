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
        .scl_wait_us = 30000,
        .flags = {
            .disable_ack_check = 0,
        },
    };

    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle));
}

void app_main(void)
{
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting System");

    // Initialize the I2C driver to work with the 
    ESP_LOGI(I2C_CONSOLE_TAG, "Initializing I2C");
    init_i2c();
    ESP_LOGI(I2C_CONSOLE_TAG, "Successfullty Initialized I2C");

    
}
