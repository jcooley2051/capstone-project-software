#include <stdio.h>
#include "esp_system.h"
#include "esp_log.h"
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "esp_rom_sys.h" // For blocking delay during asynchronous I2C operation

#include "sensor-reading-test.h"

#define SENSOR_ADDRESS 0x40
#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 7
#define I2C_CONSOLE_TAG "I2C"
#define I2C_PORT_AUTO -1

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
    .scl_speed_hz = 400000,
    .scl_wait_us = 30000,
    .flags = {
        .disable_ack_check = 1,
    },
};

i2c_master_dev_handle_t dev_handle;

void app_main(void)
{
    ESP_LOGI(I2C_CONSOLE_TAG, "Starting I2C");
    init_i2c();
    //send_reset();
    //get_and_print_temp_async();
    //send_reset();
    //vTaskDelay(1000);
    //get_and_print_temp_async();
    //get_and_print_humidity();
    xTaskCreate(&temp_task, "temp_task", 2048, NULL, 5, NULL);
}

void temp_task(void)
{
    for(;;)
    {
        get_and_print_temp_async();
        vTaskDelay(pdMS_TO_TICKS(250));
    }
}

void send_reset(void)
{
    uint8_t write_buffer[1] = {0xE3};
}

void init_i2c(void)
{
    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle));
    ESP_LOGI(I2C_CONSOLE_TAG, "I2C connection successfully established");
}

void get_and_print_temp(void)
{
    // Hex command for getting temperature reading
    uint8_t write_buffer[1] = {0xE3};
    uint8_t read_buffer[2];
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, 1, read_buffer, 2, -1));
    uint16_t temp_code = (read_buffer[0] << 8) | read_buffer[1];
    float temp_celcius = convert_to_celcius(temp_code);
    printf("Temperature: %.2f C\n", temp_celcius);
}

void get_and_print_temp_async(void)
{
    // Hex command for getting temperature reading without master hold
    uint8_t write_buffer[1] = {0xF3};
    uint8_t read_buffer[2];
    // Send read temperature request
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 1, -1));
    esp_rom_delay_us(25000);
    ESP_ERROR_CHECK(i2c_master_receive(dev_handle, read_buffer, 2, -1));
    uint16_t temp_code = (read_buffer[0] << 8) | read_buffer[1];
    float temp_celcius = convert_to_celcius(temp_code);
    printf("Temperature: %.2f C\n", temp_celcius);
}

void get_and_print_humidity(void)
{
    uint8_t write_buffer[1] = {0xE5};
    uint8_t read_buffer[2];
    ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, 1, read_buffer, 2, -1));
    uint16_t humidity_code = (read_buffer[0] << 8) | read_buffer[1];
    float relative_humidity = convert_to_humidity(humidity_code);
    printf("Relative Humidity: %0.2f %%\n", relative_humidity);
}

float convert_to_celcius(uint16_t temp_code)
{
    return ((175.25 * temp_code) / 65536.0) - 46.85;
}

float convert_to_humidity(uint16_t humidity_code)
{
    return ((125.0 * humidity_code)/65536) - 6;
}