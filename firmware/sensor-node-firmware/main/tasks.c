#include "tasks.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "timer.h"
#include "bme280-temp-sensor.h"
#include "veml7700-light-sensor.h"
#include "mqtt.h"
#include "mqtt_client.h"
#include "freertos/message_buffer.h"



MessageBufferHandle_t temp_and_humidity_message_buffer;
MessageBufferHandle_t light_message_buffer;


void temp_and_humidity_readings(void *arg)
{
    temp_and_humidity_t bne_readings;
    temp_and_humidity_message_buffer = xMessageBufferCreate(256);  // Adjust buffer size as needed
    while(1)
    {
        xEventGroupWaitBits(sensor_event_group, SENSOR_EVENT_BIT_0, pdTRUE, pdFALSE, portMAX_DELAY);
        get_temp_and_humidity(&bne_readings);
        xMessageBufferSend(temp_and_humidity_message_buffer, &bne_readings, sizeof(bne_readings), portMAX_DELAY);
    }
}

void light_readings(void *arg)
{
    light_readings_t veml_readings;
    light_message_buffer = xMessageBufferCreate(256);  // Adjust buffer size as needed
    while(1)
    {
        xEventGroupWaitBits(sensor_event_group, SENSOR_EVENT_BIT_1, pdTRUE, pdFALSE, portMAX_DELAY);
        get_light_level(&veml_readings);
        xMessageBufferSend(light_message_buffer, &veml_readings, sizeof(veml_readings), portMAX_DELAY);
    }
}

void mqtt_publish(void *arg)
{
    temp_and_humidity_t bne_readings;
    light_readings_t veml_readings;
    char message[256];
    while(1)
    {
        xMessageBufferReceive(temp_and_humidity_message_buffer, &bne_readings, sizeof(bne_readings), portMAX_DELAY);
        xMessageBufferReceive(light_message_buffer, &veml_readings, sizeof(veml_readings), portMAX_DELAY);
        snprintf(message, sizeof(message), "{ \"temperature\": %0.2f, \"humidity\": %0.2f, \"ambient_light\": %0.2f, \"white_light\": %0.2f}", bne_readings.temp_reading / 100.0, bne_readings.humidity_reading / 1024.0, veml_readings.als_reading, veml_readings.white_reading);
        esp_mqtt_client_publish(mqtt_client, "topic/test", message, 0, 1, 0);
        printf("Reading Published\n");
    }
}