#ifndef MQTT_H
#define MQTT_H

#include "mqtt_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define MQTT_TAG "MQTT:"

#define MQTT_BROKER_URI "mqtt://:1883"
#define MQTT_BROKER_USERNAME "hackerfab2025"
#define MQTT_BROKER_PASSWORD "osu2025"

// MQTT client handle
extern esp_mqtt_client_handle_t mqtt_client;

// Signal to initialize tasks after MQTT is connected
extern SemaphoreHandle_t mqtt_semaphore;

/* Sets up and configures the MQTT client */
void init_mqtt(void);

#endif
