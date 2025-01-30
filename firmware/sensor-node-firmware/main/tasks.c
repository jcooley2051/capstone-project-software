#include "tasks.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "timer.h"
#include "bme280-temp-sensor.h"
#include "veml7700-light-sensor.h"
#include "ih-ipm-particle-sensor.h"
#include "mqtt.h"
#include "mqtt_client.h"
#include "freertos/message_buffer.h"
#include "esp_log.h"


#define REGULAR_MESSAGE_BUFFER_SIZE 256

MessageBufferHandle_t temp_and_humidity_message_buffer;
MessageBufferHandle_t light_message_buffer;
MessageBufferHandle_t particle_count_message_buffer;

int error_counter = 0;


void temp_and_humidity_readings(void *arg)
{
    temp_and_humidity_t bne_readings;
    temp_and_humidity_message_buffer = xMessageBufferCreate(REGULAR_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        xEventGroupWaitBits(sensor_event_group, SENSOR_EVENT_BIT_0, pdTRUE, pdFALSE, portMAX_DELAY);
        ESP_LOGI("temp_and_humidity_readings", "Getting temp and humidity reading");
        get_temp_and_humidity(&bne_readings);
        xMessageBufferSend(temp_and_humidity_message_buffer, &bne_readings, sizeof(bne_readings), portMAX_DELAY);
    }
}

void light_readings(void *arg)
{
    light_readings_t veml_readings;
    light_message_buffer = xMessageBufferCreate(REGULAR_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        xEventGroupWaitBits(sensor_event_group, SENSOR_EVENT_BIT_1, pdTRUE, pdFALSE, portMAX_DELAY);
        ESP_LOGI("light_readings", "Getting light reading");
        ESP_LOGI("temp_and_humidity_readings", "Getting temp and humidity reading");
        get_light_level(&veml_readings);
        xMessageBufferSend(light_message_buffer, &veml_readings, sizeof(veml_readings), portMAX_DELAY);
    }
}

void particle_count_readings(void *arg)
{
    uint16_t reading;
    particle_count_message_buffer = xMessageBufferCreate(REGULAR_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        ESP_LOGI("mqtt_publish", "Reading Published");
        xEventGroupWaitBits(sensor_event_group, SENSOR_EVENT_BIT_2, pdTRUE, pdFALSE, portMAX_DELAY);
        ESP_LOGI("particle_count_readings", "Getting particle count reading");
        get_particle_count(&reading);
        xMessageBufferSend(particle_count_message_buffer, &reading, sizeof(reading), portMAX_DELAY);
    }
}

void mqtt_publish(void *arg)
{
    temp_and_humidity_t bne_readings;
    light_readings_t veml_readings;
    uint16_t particle_count_readings;
    char message[256];
    while(1)
    {
        if (xMessageBufferReceive(temp_and_humidity_message_buffer, &bne_readings, sizeof(bne_readings), portMAX_DELAY) != sizeof(bne_readings))
        {
            ESP_LOGE("mqtt_publish", "Error: unexpected number of bytes for bne readings");
            error_counter++;
        }
        if (xMessageBufferReceive(light_message_buffer, &veml_readings, sizeof(veml_readings), portMAX_DELAY) != sizeof(veml_readings))
        {
            ESP_LOGE("mqtt_publish", "Error: unexpected number of bytes for veml reading");
            error_counter++;
        }
        if (xMessageBufferReceive(particle_count_message_buffer, &particle_count_readings, sizeof(particle_count_readings), portMAX_DELAY) != sizeof(particle_count_readings))
        {
            ESP_LOGE("mqtt_publish", "Error: unexpected number of bytes for particle count reading");
            error_counter++;
        }
        if (snprintf(message, sizeof(message), "{ \"temperature\": %0.2f, \"humidity\": %0.2f, \"ambient_light\": %0.2f, \"white_light\": %0.2f}, \"particle_count\": %u", bne_readings.temp_reading / 100.0, bne_readings.humidity_reading / 1024.0, veml_readings.als_reading, veml_readings.white_reading, particle_count_readings) < 0)
        {
            ESP_LOGE("mqtt_publish","Error: something happened while generating mqtt message");
            error_counter++;
        }
        int ret = esp_mqtt_client_publish(mqtt_client, "topic/test", message, 0, 1, 0);
        if (ret == -1)
        {
            ESP_LOGE("mqtt_publish", "Error: Failed to publish to MQTT broker");
            error_counter++;
        }
        else if (ret == -2)
        {
            ESP_LOGE("mqtt_publish", "Error: MQTT outbox full");
            error_counter++;
        }
        if (error_counter > ERROR_COUNT_THRESHOLD)
        {
            ESP_LOGE("mqtt_publish", "Error: We are getting lots of errors, rebooting...");
            esp_restart();
        }
        ESP_LOGI("mqtt_publish", "Reading Published");
    }
}