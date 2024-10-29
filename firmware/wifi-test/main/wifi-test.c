#include <stdio.h>

#include "wifi-test.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_err.h"
#include "esp_log.h"
#include "mqtt_client.h"
#include "FreeRTOS/FreeRTOS.h"

// Wifi credentials
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

// For logging
static const char *TAG = "wifi_station";

// Wifi connection retries
static int s_retry_num = 0;

// MQTT client handle
esp_mqtt_client_handle_t mqtt_client;

void app_main(void)
{
    // NVS is used to store wifi configuration info
    // Honestly, I'm not sure if we need it, but the default wifi settings require it, and it's not hurting anything
    init_flash();

    // Initialize wifi driver and register event handlers
    init_wifi();

    // Configure the wifi and connect to the network
    config_wifi();

    // Initialize the MQTT driver and connect to the broker
    init_mqtt();

    int count = 0;
    // Send test messages to broker every second
    while(1)
    {
        // Publish the test message to /topic/test on the MQTT broker
        esp_mqtt_client_publish(client, "/topic/test", sprintf("Hello from ESP32 | Count: %d", count), 0, 1, 0);
        count++;
        vTaskDelay(1000);
    }
}

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
        s_retry_num = 0;
    }
}

void init_mqtt()
{
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = "mqtt://192.168.50.170:1883",  // Set your Mosquitto broker's IP address here
    };
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
            .password = WIFI_PASSWORD,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };

    // Set the ESP to station mode (i.e. a device connecting to a network)
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));

    // Set the configuration of the station (i.e. the info that is needed to connect to network)
    ESP_ERROR_CHECK(esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_cfg));

    // Actually start the wifi with the current configuration
    ESP_ERROR_CHECK(esp_wifi_start());

}
