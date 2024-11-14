#include <stdio.h>
#include "sensor-readings-over-mqtt-test.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "mqtt_client.h"
#include "FreeRTOS/FreeRTOS.h"
#include "driver/i2c_master.h"


#define I2C_CONSOLE_TAG "I2C"
#define SYSTEM_CONSOLE_TAG "System"
#define BME_CONSOLE_TAG "BME280"

// Wifi credentials
#define WIFI_SSID "Hackerfab Monitor"
#define WIFI_PASSWORD ""

#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5
#define I2C_PORT_AUTO -1
#define BME_SENSOR_ADDRESS 0x77

// Compensation factors from BME280 Sensor
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
i2c_master_dev_handle_t bme_dev_handle;

SemaphoreHandle_t wifi_mqtt_semaphore;

//                                          I2C Stuff

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
        .device_address = BME_SENSOR_ADDRESS,
        .scl_speed_hz = 400000,
        .scl_wait_us = 30000,
        .flags = {
            .disable_ack_check = 0,
        },
    };

    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &bme_dev_handle));
}


//                                        WiFi and MQTT stuff

// For logging
static const char *TAG = "wifi_station";

// Wifi connection retries
static int s_retry_num = 0;

// MQTT client handle
esp_mqtt_client_handle_t mqtt_client;

static void mqtt_event_handler(void* handler_args, esp_event_base_t base, int32_t event_id, void* event_data) {
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client = event->client;
    switch (event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
            // Publish a message once connected
            esp_mqtt_client_publish(client, "/topic/test", "Hello from ESP32", 0, 1, 0);
            break;
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
            break;
        default:
            break;
    }
}

static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < EXAMPLE_MAXIMUM_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "retry to connect to the AP");
        } else {
            ESP_LOGI(TAG, "failed to connect to the AP");
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        xSemaphoreGive(wifi_mqtt_semaphore);
        s_retry_num = 0;
    }
}

void init_mqtt()
{
    
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = "mqtt://10.42.0.1:1883",  // Set your Mosquitto broker's IP address here
    };
    
   /*
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = "mqtt://test.mosquitto.org:1883",  // Set your Mosquitto broker's IP address here
    };
    */
   
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
}

void init_flash()
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}


void init_wifi()
{
    wifi_init_config_t wifi_init_cfg = WIFI_INIT_CONFIG_DEFAULT();

    // Create LwIP core task and initialize LwIp related work
    ESP_ERROR_CHECK(esp_netif_init());

    // Create defauly system event task to handle wifi events
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // Create default network interface for wifi station mode
    esp_netif_create_default_wifi_sta();

    // Create driver task and initialize with default config
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_init_cfg));

    // Register event handlers for IP and Wifi events
    esp_event_handler_instance_t instance_got_ip;
    esp_event_handler_instance_t instance_any_id;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                    IP_EVENT_STA_GOT_IP,
                                                    &wifi_event_handler,
                                                    NULL,
                                                    &instance_got_ip));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                    ESP_EVENT_ANY_ID,
                                                    &wifi_event_handler,
                                                    NULL,
                                                    &instance_any_id));
}

void config_wifi()
{
    // Set the wifi SSID, PASSWORD, and authorization mode (WPA2). Other settings
    // will be default
    wifi_config_t wifi_cfg = {
        .sta = {
            .ssid = WIFI_SSID,
            //.password = WIFI_PASSWORD,
            //.threshold.authmode = WIFI_AUTH_WPA2_PSK,
            .threshold.authmode = WIFI_AUTH_OPEN,
        },
    };

    // Set the ESP to station mode (i.e. a device connecting to a network)
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));

    // Set the configuration of the station (i.e. the info that is needed to connect to network)
    ESP_ERROR_CHECK(esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_cfg));

    // Actually start the wifi with the current configuration
    ESP_ERROR_CHECK(esp_wifi_start());

}

//                                      BME280 Stuff

void configure_bme280(void)
{
    // Holds bytes for writing
    uint8_t write_buffer[2];

    // Configure standby time (20ms) and filter (Off) 0b11100000
    write_buffer[0] = 0xF5; // Register Address
    write_buffer[1] = 0xD0;
    ESP_ERROR_CHECK(i2c_master_transmit(bme_dev_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Configure Temperature Oversampling (16x) and mode (Normal) 0b10100011
    write_buffer[0] = 0xF4; // Register Address
    write_buffer[1] = 0xA3;
    ESP_ERROR_CHECK(i2c_master_transmit(bme_dev_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));

    // Configure Humidity Oversampling (16x) 0b00000101
    write_buffer[0] = 0xF2; // Register Address
    write_buffer[1] = 0x05;
    ESP_ERROR_CHECK(i2c_master_transmit(bme_dev_handle, write_buffer, sizeof(write_buffer), portMAX_DELAY));
}

void read_compensation(void)
{
    uint8_t write_buffer[1];
    uint8_t read_buffer[2];

    // Read dig_T1
    write_buffer[0] = 0x88;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T1 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_T1);

    // Read dig_T2
    write_buffer[0] = 0x8A;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T2 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_T2);

    // Read dig_T3
    write_buffer[0] = 0x8C;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_T3 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_T3);     

    // Read dig_H1
    write_buffer[0] = 0xA1;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H1 = read_buffer[0];
    printf("%d\n", dig_H1);

    // Read dig_H2
    write_buffer[0] = 0xE1;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H2 = (read_buffer[1] << 8) | read_buffer[0];
    printf("%d\n", dig_H2);

    // Read dig_H3
    write_buffer[0] = 0xE3;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
    dig_H3 = read_buffer[0];
    printf("%d\n", dig_H3);

    // Read dig_H4
    write_buffer[0] = 0xE4;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H4 = (read_buffer[0] << 4) | (read_buffer[1] & 0xF);
    printf("%d\n", dig_H4);

    // Read dig_H5
    write_buffer[0] = 0xE5;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 2, portMAX_DELAY));
    dig_H5 = (read_buffer[1] << 4) | (read_buffer[0] & 0xF0 >> 4);
    printf("%d\n", dig_H5);

    // Read dig_H6
    write_buffer[0] = 0xE7;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, sizeof(write_buffer), read_buffer, 1, portMAX_DELAY));
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
        ESP_ERROR_CHECK(i2c_master_transmit_receive(bme_dev_handle, write_buffer, 1, read_buffer, 8, portMAX_DELAY));
        print_sensor_readings(read_buffer);
        vTaskDelay(1000 / portTICK_PERIOD_MS);  // 250ms delay
    }
}

void print_sensor_readings(uint8_t *readings)
{
    int32_t t_fine; // Fine temperature to use in humidity calculation

    // Print temperature readings (for explaination, visit BME280 datasheet)
    int32_t temp_reading = (readings[3] << 12) | (readings[4] << 4) | (readings[5] & 0xF0 >> 4);
    int32_t var1, var2, temp;
    var1 = ((((temp_reading >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
    var2 = (((((temp_reading >> 4) - ((int32_t)dig_T1)) * ((temp_reading >> 4) - ((int32_t)dig_T1))) >> 12) * ((int32_t)dig_T3)) >> 14;
    t_fine = var1 + var2;
    // resolution is 0.01 DegC, so "1234" equals 12.34 DegC
    temp = (t_fine * 5 + 128) >> 8;
    printf("Temp: %0.2f C\n", temp/100.0);
    char message[50];
    snprintf(message, sizeof(message), "%0.2f", temp / 100.0);

    printf("Publishing\n");
    // Publish the formatted temperature message to the MQTT broker
    esp_mqtt_client_publish(mqtt_client, "/readings/temp", message, 0, 1, 0);
    // esp_mqtt_client_publish(mqtt_client, "/readings/temp", sprintf("Temperature %d", temp/100), 0, 1, 0);


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
    snprintf(message, sizeof(message), "%0.2f", humidity / 1024.0);
    esp_mqtt_client_publish(mqtt_client, "/readings/humidity", message, 0, 1, 0);
}



void app_main(void)
{

    wifi_mqtt_semaphore = xSemaphoreCreateBinary();

    if (wifi_mqtt_semaphore == NULL)
    {
        abort();
    }

    // NVS is used to store wifi configuration info
    // Honestly, I'm not sure if we need it, but the default wifi settings require it, and it's not hurting anything
    init_flash();

    // Initialize wifi driver and register event handlers
    init_wifi();

    // Configure the wifi and connect to the network
    config_wifi();

    xSemaphoreTake(wifi_mqtt_semaphore, portMAX_DELAY);
    ESP_LOGI("SYSTEM", "Initializing MQTT");

    // Initialize the MQTT driver and connect to the broker
    init_mqtt();


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
    xTaskCreate(bme_readings_task, "Temp/Humidity Readings Task", 65536, NULL, 5, NULL);
}
