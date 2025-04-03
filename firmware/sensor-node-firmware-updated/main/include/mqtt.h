#ifndef MQTT_H
#define MQTT_H

#include "mqtt_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "config.h"

#define MQTT_TAG "MQTT:"

#define MQTT_BROKER_URI "mqtt://10.42.0.1:1337"
#define MQTT_BROKER_USERNAME "hackerfab2025"
#define MQTT_BROKER_PASSWORD "osu2025"

#if defined(PHOTOLITHOGRAPHY) && defined(SPUTTERING) && defined(SPIN_COATING)
    #define MQTT_TOPIC "topic/test"
    #define BATTERY_TOPIC "topic/test_battery"
#else
#ifdef PHOTOLITHOGRAPHY 
    #define MQTT_TOPIC "topic/PL"
    #define BATTERY_TOPIC "topic/PL_battery"
#endif
#ifdef SPUTTERING 
    #define MQTT_TOPIC "topic/SP"
    #define BATTERY_TOPIC "topic/SP_battery"
#endif
#ifdef SPIN_COATING 
    #define MQTT_TOPIC "topic/SC"
    #define BATTERY_TOPIC "topic/SC_battery"
#endif
#endif

// MQTT client handle
extern esp_mqtt_client_handle_t mqtt_client;

// Signal to initialize tasks after MQTT is connected
extern SemaphoreHandle_t mqtt_semaphore;

/* Sets up and configures the MQTT client */
void init_mqtt(void);

#endif
