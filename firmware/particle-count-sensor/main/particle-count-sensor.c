/* I2C does not seem to work. If you wanna give it a go be my guest, but after 10+ hours of attempting to diagnose the problem from teh 4 page user manual and useless forum posts I'm done

#include <stdio.h>
#include "esp_log.h"
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "particle-count-sensor.h"

#define I2C_CONSOLE_TAG "I2C"
#define SYSTEM_CONSOLE_TAG "System"
#define VEML_CONSOLE_TAG "VEML7700"

#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5
#define I2C_PORT_AUTO -1
#define SENSOR_ADDRESS 0x08

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

void configure_sensor(void)
{
    uint8_t unsleep_buffer[4] = {0x00};
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, unsleep_buffer, 1, portMAX_DELAY));
    vTaskDelay(50 / portTICK_PERIOD_MS);
    uint8_t write_buffer[] = {0x10, 0x00, 0x10, 0x05, 0x00, 0xF6};
    ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 6, portMAX_DELAY));
    // Placeholder in case we decide to customize configuration
}

void sensor_readings_task(void *arg)
{
        uint8_t write_buffer[3] = {0x10, 0x03, 0x00};
        uint8_t write_buffer2[1] = {0x11};
    uint8_t read_buffer[30];
    
    while(1)
    {
        ESP_LOGI("VEML_CONSOLE_TAG", "Thing");
        ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 3, portMAX_DELAY));
        ESP_ERROR_CHECK(i2c_master_transmit_receive(dev_handle, write_buffer2, 1, read_buffer, 30, portMAX_DELAY));
        //ESP_ERROR_CHECK(i2c_master_transmit(dev_handle, write_buffer, 4, portMAX_DELAY));
        //print_sensor_reading(read_buffer);
        vTaskDelay(750 / portTICK_PERIOD_MS);  // 750ms delay (600ms refresh rate MAX)
    }
}

void print_sensor_reading(uint8_t *read_buffer)
{
    uint16_t reading = (read_buffer[0] << 8) | read_buffer[1];
    printf("Particle Count: %d", reading);
}

void app_main(void)
{
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting System");

    // Initialize the I2C driver to work with the 
    ESP_LOGI(I2C_CONSOLE_TAG, "Initializing I2C");
    init_i2c();
    ESP_LOGI(I2C_CONSOLE_TAG, "Successfullty Initialized I2C");

    vTaskDelay(1000 / portTICK_PERIOD_MS);

    // Configure VEML7700 ambient light sensor
    ESP_LOGI(VEML_CONSOLE_TAG, "Configuring Particle Count Sensor");
    configure_sensor();
    ESP_LOGI(VEML_CONSOLE_TAG, "Successfully Configured Particle Count Sensor");

    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting Readings Task");
    xTaskCreate(sensor_readings_task, "Temp/Particle Readings Task", 2048, NULL, 5, NULL);
}

*/

// UART



#include <stdio.h>
#include "esp_log.h"
#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "particle-count-sensor.h"
#include "driver/gpio.h"

#define UART_CONSOLE_TAG "UART"
#define SYSTEM_CONSOLE_TAG "System"
#define SENSOR_CONSOLE_TAG "VEML7700"

#define UART_PORT UART_NUM_1
#define TX_GPIO_PIN 17
#define RX_GPIO_PIN 16
#define UART_BAUD_RATE 1200
#define UART_BUF_SIZE 256

// UART configuration
void init_uart(void)
{
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };

    // Install UART driver
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, UART_BUF_SIZE, 0, 0, NULL, 0));
    // Configure UART parameters
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &uart_config));
    // Set UART pins
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, TX_GPIO_PIN, RX_GPIO_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
}

void configure_sensor(void)
{
    vTaskDelay(25 / portTICK_PERIOD_MS);

    // Send start measurement command: FE A5 00 11 B6
    uint8_t start_measurement_cmd[] = {0xFE, 0xA5, 0x00, 0x11, 0xB6};
    uart_write_bytes(UART_PORT, (const char *)start_measurement_cmd, sizeof(start_measurement_cmd));
    gpio_set_drive_capability(TX_GPIO_PIN, GPIO_DRIVE_CAP_3);
    gpio_set_drive_capability(RX_GPIO_PIN, GPIO_DRIVE_CAP_3);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    ESP_LOGI(UART_CONSOLE_TAG, "Sent start measurement command");
}

void sensor_readings_task(void *arg)
{
    //uint8_t read_data_cmd[] = {0xFE, 0xA5, 0x00, 0x07, 0xA6};
    uint8_t read_data_cmd[] = {0xFE, 0xA5, 0x00, 0x00, 0xA5};
    uint8_t read_buffer[7];  // 12 bytes: Header + PM1.0, PM2.5, PM4.0, PM10 + Checksum

    while (1)
    {
        // Send read data command
        uart_write_bytes(UART_PORT, (const char *)read_data_cmd, sizeof(read_data_cmd));

        // Wait for the response (12 bytes expected)
        int length = uart_read_bytes(UART_PORT, read_buffer, sizeof(read_buffer), 100 / portTICK_PERIOD_MS);
        if (length == 7)
        {
            // Validate response header and length
            if (read_buffer[0] == 0xFE && read_buffer[1] == 0xA5 && read_buffer[2] == 0x02)
            {
                print_sensor_reading(read_buffer);
            }
            else
            {
                ESP_LOGE(UART_CONSOLE_TAG, "Invalid response structure");
            }
        }
        else
        {
            printf("%d", length);
            ESP_LOGE(UART_CONSOLE_TAG, "Failed to read sensor data");
        }

        vTaskDelay(1000 / portTICK_PERIOD_MS);  // 1-second delay between readings
    }
}

void print_sensor_reading(uint8_t *read_buffer)
{
    int16_t pm2_5 = read_buffer[4]*256 + read_buffer[5];
    printf("PM2.5: %d µg/m³\n", pm2_5);
}

void app_main(void)
{
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting System");

    // Initialize the UART driver
    ESP_LOGI(UART_CONSOLE_TAG, "Initializing UART");
    init_uart();
    ESP_LOGI(UART_CONSOLE_TAG, "Successfully Initialized UART");

    // Configure the particle count sensor
    ESP_LOGI(SENSOR_CONSOLE_TAG, "Configuring Particle Count Sensor");
    configure_sensor();
    ESP_LOGI(SENSOR_CONSOLE_TAG, "Successfully Configured Particle Count Sensor");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    ESP_LOGI(SYSTEM_CONSOLE_TAG, "Starting Readings Task");
    xTaskCreate(sensor_readings_task, "Particle Readings Task", 2048, NULL, 5, NULL);
}
