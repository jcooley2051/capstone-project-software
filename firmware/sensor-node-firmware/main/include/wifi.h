#ifndef WIFI_H
#define WIFI_H

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

// Wifi credentials, make better solution later
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

#define WIFI_EVENT_TAG "WiFi Station:"

#define MAX_CONNECTION_RETRY_COUNT 10

extern SemaphoreHandle_t wifi_semaphore;
void init_flash(void);
void init_wifi(void);
void config_wifi(void);



#endif