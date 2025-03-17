#ifndef MQTT_H
#define MQTT_H

#include "mqtt_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "config.h"

#define MQTT_TAG "MQTT:"

#define MQTT_BROKER_URI "mqtt://192.168.50.170:1883"

#if defined(PHOTOLITHOGRAPHY) && defined(SPUTTERING) && defined(SPIN_COATING)
    #define MQTT_TOPIC "topic/test"
#else
#ifdef PHOTOLITHOGRAPHY 
    #define MQTT_TOPIC "topic/photolithography"
#endif
#ifdef SPUTTERING 
    #define MQTT_TOPIC "topic/sputtering"
#endif
#ifdef SPIN_COATING 
    #define MQTT_TOPIC "topic/spin_coating"
#endif
#endif

// MQTT client handle
extern esp_mqtt_client_handle_t mqtt_client;

// Signal to initialize tasks after MQTT is connected
extern SemaphoreHandle_t mqtt_semaphore;

/* Sets up and configures the MQTT client */
void init_mqtt(void);

#endif