
#include "wifi.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_log.h"


// Number of connection retrys
static int s_retry_num = 0;

// Semaphore used to hold off starting MQTT client until WiFi is connected
SemaphoreHandle_t wifi_semaphore;

// Initialize NVS storage for wifi credentials
void init_flash(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        esp_wifi_connect();
        ESP_LOGI(WIFI_EVENT_TAG, "retry to connect to the AP");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(WIFI_EVENT_TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        xSemaphoreGive(wifi_semaphore);
        s_retry_num = 0;
    }
}

void init_wifi(void)
{
    wifi_semaphore = xSemaphoreCreateBinary();

    if (wifi_semaphore == NULL)
    {
        ESP_LOGE("FreeRTOS", "Failed to initialize WiFi semaphore. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }

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

void config_wifi(void)
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