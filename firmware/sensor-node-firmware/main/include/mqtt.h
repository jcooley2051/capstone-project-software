#ifndef MQTT_H
#define MQTT_H

#include "mqtt_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define MQTT_TAG "MQTT:"

#define MQTT_BROKER_URI "mqtt://192.168.50.170:1883"

// MQTT client handle
extern esp_mqtt_client_handle_t mqtt_client;
extern SemaphoreHandle_t mqtt_semaphore;

void init_mqtt(void);

#endif