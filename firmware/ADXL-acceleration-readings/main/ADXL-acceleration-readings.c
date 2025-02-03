#include <stdio.h>
#include "esp_log.h"
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "ADXL-acceleration-readings.h"
#include "wifi.h"
#include "mqtt.h"

#define I2C_CONSOLE_TAG "I2C"
#define SYSTEM_CONSOLE_TAG "System"
#define VEML_CONSOLE_TAG "VEML7700"

#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5
#define I2C_PORT_AUTO -1
#define SENSOR_ADDRESS 0x1D


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
    uint8_t write_buffer[2];
    write_buffer[0] = 0x2D;
    write_buffer[1] = 0x92;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 2, portMAX_DELAY));

    write_buffer[0] = 0x28;
    write_buffer[1] = 0x01;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 2, portMAX_DELAY));

    write_buffer[0] = 0x2C;
    write_buffer[1] = 0x01;
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 2, portMAX_DELAY));
    // Placeholder in case we decide to customize configuration
}

void veml_readings_task(void *arg)
{
    uint8_t write_buffer[1] = {0x08};
    uint8_t read_buffer[9*500];
    // One extra for the null terminator
    char mqtt_buffer[9*500*2 + 1];
    const TickType_t period_ticks = pdMS_TO_TICKS(2); // 2 ms in ticks
    const TickType_t period_ticks2 = pdMS_TO_TICKS(1000); // 1.25 ms in ticks
    TickType_t last_wake_time = xTaskGetTickCount();      // Initialize last wake time
    TickType_t last_wake_time2 = xTaskGetTickCount();   
    int count = 0;
    while(1)
    {
        int i = 0;
        while(count < 500)
        {
            ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer, 1, &read_buffer[i], 9, portMAX_DELAY));
            //print_sensor_reading(read_buffer);
            vTaskDelayUntil(&last_wake_time, period_ticks);
            i += 9;
            count++;
        }
        i = 0;
        count = 0;
        encode_to_hex(read_buffer, 9*500, mqtt_buffer);
        esp_mqtt_client_publish(mqtt_client, "your/topic", mqtt_buffer, strlen(mqtt_buffer), 1, 0);
        vTaskDelayUntil(&last_wake_time2, period_ticks2);
    }

}

void encode_to_hex(const uint8_t *buffer, size_t buffer_len, char *output) {
    const char *hex_chars = "0123456789ABCDEF";
    for (size_t i = 0; i < buffer_len; ++i) {
        output[i * 2] = hex_chars[(buffer[i] >> 4) & 0x0F];
        output[i * 2 + 1] = hex_chars[buffer[i] & 0x0F];
    }
    output[buffer_len * 2] = '\0'; // Null-terminate the string
}

void print_sensor_reading(uint8_t *read_buffer)
{
    int32_t x_data = (read_buffer[0] << 12) | (read_buffer[1] << 4) | (read_buffer[2] >> 4);
    int32_t y_data = (read_buffer[3] << 12) | (read_buffer[4] << 4) | (read_buffer[5] >> 4);
    int32_t z_data = (read_buffer[6] << 12) | (read_buffer[7] << 4) | (read_buffer[8] >> 4);
    if (x_data & 0x80000) x_data |= 0xFFF00000; // Sign-extend if the 20th bit is set
    if (y_data & 0x80000) y_data |= 0xFFF00000; // Sign-extend if the 20th bit is set
    if (z_data & 0x80000) z_data |= 0xFFF00000; // Sign-extend if the 20th bit is set

    printf("Acceleration: X %0.2f, Y: %0.2f, Z: %0.2f \n", ((float)x_data / 256000)*9.81 , ((float)y_data / 256000)*9.81, ((float)z_data / 256000)*9.81);
}

void app_main(void)
{
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting System");

    init_flash();
    init_wifi();
    config_wifi();
    init_mqtt();
    

    // Initialize the I2C driver to work with the 
    ESP_LOGI(I2C_CONSOLE_TAG, "Initializing I2C");
    init_i2c();
    ESP_LOGI(I2C_CONSOLE_TAG, "Successfullty Initialized I2C");

    // Configure VEML7700 ambient light sensor
    ESP_LOGI(VEML_CONSOLE_TAG, "Configuring VEML7700");
    configure_veml7700();
    ESP_LOGI(VEML_CONSOLE_TAG, "Successfully Configured VEML7700");

    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting Readings Task");
    xTaskCreate(veml_readings_task, "Temp/Humidity Readings Task", 65536, NULL, 5, NULL);
}
