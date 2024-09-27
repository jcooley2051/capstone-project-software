#include <stdio.h>
#include "esp_system.h"
#include "esp_log.h"
#include "driver/i2c_master.h"

#include "sensor-reading-test.h"

#define SENSOR_ADDRESS 0x40
#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 7
#define I2C_CONSOLE_TAG "I2C"

i2c_master_bus_config_t i2c_mst_config = {
    .clk_source = I2C_CLK_SRC_DEFAULT,
    .i2c_port = I2C_PORT_AUTO,
    .scl_io_num = SCL_GPIO_PIN,
    .sda_io_num = SDA_GPIO_PIN,
    .glitch_ignore_cnt = 7,
    .flags.enable_internal_pullup = true,
};

i2c_master_bus_handle_t bus_handle;

i2c_device_config_t dev_cfg = {
    .dev_addr_length = I2C_ADDR_BIT_LEN_7,
    .device_address = SENSOR_ADDRESS,
    .scl_speed_hz = 100000,
};

i2c_master_dev_handle_t dev_handle;

void app_main(void)
{
    ESP_LOGI(I2C_CONSOLE_TAG, "Starting I2C");
    init_i2c();
}

void init_i2c(void)
{
    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle));
    ESP_LOGI(I2C_CONSOLE_TAG, "I2C connection successfully established");
}
