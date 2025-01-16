#ifndef TIMER_H
#define TIMER_H
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/timers.h"


extern EventGroupHandle_t sensor_event_group;
extern TimerHandle_t sensor_timer;

// How often to trigger readings
#define UPDATE_PERIOD_MS 1000

// Event bit mask (one bit per task)
#define SENSOR_EVENT_BIT_0 (1 << 0)
#define SENSOR_EVENT_BIT_1 (1 << 1)

void sensor_timer_callback(TimerHandle_t xTimer);
void init_timer(void);

#endif