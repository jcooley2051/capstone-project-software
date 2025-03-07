#ifndef WIFI_H
#define WIFI_H

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

// Wifi credentials
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

#define WIFI_EVENT_TAG "WiFi Station:"

// Maximum number of times to try to reconnect to WiFi before restarting microcontroller
#define MAX_CONNECTION_RETRY_COUNT 10

// Signal to proceed with MQTT initialization
extern SemaphoreHandle_t wifi_semaphore;

/* Initializes flash storage for the microcontroller, which is used to Configuration information used by event handler,
    must be called before init_wifi
 */
void init_flash(void);
/* Initializes the WiFi driver, must be called before config_wifi*/
void init_wifi(void);
/* Configures the WiFi setup for the device such as password and network type */
void config_wifi(void);



#endif