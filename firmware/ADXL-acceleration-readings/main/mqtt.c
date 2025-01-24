#include "mqtt_client.h"
#include "mqtt.h"
#include "esp_log.h"


esp_mqtt_client_handle_t mqtt_client;
SemaphoreHandle_t mqtt_semaphore;


static void mqtt_event_handler(void* handler_args, esp_event_base_t base, int32_t event_id, void* event_data) {
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client = event->client;
    switch (event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(MQTT_TAG, "MQTT_EVENT_CONNECTED");
            // Publish a message once connected
            //esp_mqtt_client_publish(client, "/topic/test", "Hello from ESP32", 0, 1, 0);
            xSemaphoreGive(mqtt_semaphore);
            break;
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI(MQTT_TAG, "MQTT_EVENT_DISCONNECTED");
            break;
        default:
            break;
    }
}


void init_mqtt(void)
{
    mqtt_semaphore = xSemaphoreCreateBinary();

    if (mqtt_semaphore == NULL)
    {
        ESP_LOGE("FreeRTOS", "Failed to initialize mqtt semaphore. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }

    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URI,  // Set your Mosquitto broker's IP address here
    };
   
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
}