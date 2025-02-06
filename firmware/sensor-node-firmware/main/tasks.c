#include "tasks.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "timer.h"
#include "bme280-temp-sensor.h"
#include "veml7700-light-sensor.h"
#include "ih-ipm-particle-sensor.h"
#include "adxl-vibration-sensor.h"
#include "mqtt.h"
#include "mqtt_client.h"
#include "freertos/message_buffer.h"
#include "esp_log.h"


#define REGULAR_MESSAGE_BUFFER_SIZE 256
#define LARGE_MESSAGE_BUFFER_SIZE 9500

MessageBufferHandle_t temp_and_humidity_message_buffer;
MessageBufferHandle_t light_message_buffer;
MessageBufferHandle_t particle_count_message_buffer;
MessageBufferHandle_t vibration_message_buffer;

int error_counter = 0;


void temp_and_humidity_readings(void *arg)
{
    temp_and_humidity_t bne_readings;
    temp_and_humidity_message_buffer = xMessageBufferCreate(REGULAR_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        // Wait for the timer to trigger this task to run once per second
        xEventGroupWaitBits(sensor_event_group, EVENT_BIT_READY_TEMP, pdTRUE, pdFALSE, portMAX_DELAY);
        ESP_LOGI("temp_and_humidity_readings", "Getting temp and humidity reading");
        get_temp_and_humidity(&bne_readings);
        // Signal to the vibration task that we are finished reading the temperature and humidity
        xEventGroupSetBits(sensor_event_group, EVENT_BIT_DONE_TEMP);
        xMessageBufferSend(temp_and_humidity_message_buffer, &bne_readings, sizeof(bne_readings), portMAX_DELAY);
    }
}

void light_readings(void *arg)
{
    light_readings_t veml_readings;
    light_message_buffer = xMessageBufferCreate(REGULAR_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        // Wait for the timer to trigger this task to run once per second
        xEventGroupWaitBits(sensor_event_group, EVENT_BIT_READY_LIGHT, pdTRUE, pdFALSE, portMAX_DELAY);
        ESP_LOGI("light_readings", "Getting light reading");
        get_light_level(&veml_readings);
        // Signal to the vibration task that we are finished reading light
        xEventGroupSetBits(sensor_event_group, EVENT_BIT_DONE_LIGHT);
        xMessageBufferSend(light_message_buffer, &veml_readings, sizeof(veml_readings), portMAX_DELAY);
    }
}

void particle_count_readings(void *arg)
{
    uint16_t reading;
    particle_count_message_buffer = xMessageBufferCreate(REGULAR_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        // Wait for the timer to trigger this task to run once per second
        xEventGroupWaitBits(sensor_event_group, EVENT_BIT_READY_PARTICLE, pdTRUE, pdFALSE, portMAX_DELAY);
        ESP_LOGI("particle_count_readings", "Getting particle count reading");
        get_particle_count(&reading);
        // Signal to vibration task that we are finished reading the particle count
        xEventGroupSetBits(sensor_event_group, EVENT_BIT_DONE_PARTICLE);
        xMessageBufferSend(particle_count_message_buffer, &reading, sizeof(reading), portMAX_DELAY);
    }
}

void vibration_readings(void *arg)
{
    uint8_t read_buffer[ADXL_READING_SIZE_BYTES * ADXL_NUM_READINGS];
    // One extra for the null terminator
    char hex_buffer[ADXL_READING_SIZE_BYTES * ADXL_NUM_READINGS * 2 + 1];
    vibration_message_buffer = xMessageBufferCreate(LARGE_MESSAGE_BUFFER_SIZE);  // Adjust buffer size as needed
    while(1)
    {
        // Wait for all other tasks to complete their readings so that we can get an uninterrupted run of the vibration readings 
        xEventGroupWaitBits(sensor_event_group, EVENT_BIT_DONE_TEMP | EVENT_BIT_DONE_LIGHT | EVENT_BIT_DONE_PARTICLE, pdTRUE, pdTRUE, portMAX_DELAY);
        ESP_LOGI("vibration_readings", "Getting vibration reading");
        get_vibration_readings(read_buffer);
        encode_to_hex(read_buffer, sizeof(read_buffer), hex_buffer);
        xMessageBufferSend(vibration_message_buffer, hex_buffer, sizeof(hex_buffer), portMAX_DELAY);
    }
}

void mqtt_publish(void *arg)
{
    temp_and_humidity_t bne_readings;
    light_readings_t veml_readings;
    uint16_t particle_count_readings;
    char vibration_readings[ADXL_READING_SIZE_BYTES * ADXL_NUM_READINGS * 2 + 1];
    char message[1024 + sizeof(vibration_readings)];
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
        if (xMessageBufferReceive(vibration_message_buffer, vibration_readings, sizeof(vibration_readings), portMAX_DELAY) != sizeof(vibration_readings))
        {
            ESP_LOGE("mqtt_publish", "Error: unexpected number of bytes for vibration reading");
            error_counter++;
        }
        if (snprintf(message, sizeof(message), "{ \"temperature\": %0.2f, \"humidity\": %0.2f, \"ambient_light\": %0.2f, \"white_light\": %0.2f, \"particle_count\": %u, \"vibration\": \"%s\" }", bne_readings.temp_reading / 100.0, bne_readings.humidity_reading / 1024.0, veml_readings.als_reading, veml_readings.white_reading, particle_count_readings, vibration_readings) < 0)
        {
            ESP_LOGE("mqtt_publish","Error: something happened while generating mqtt message");
            error_counter++;
        }
        ESP_LOGI("mqtt_publish", "Publishing");
        int ret = esp_mqtt_client_publish(mqtt_client, "/topic/test", message, 0, 1, 0);
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
        
    }
}