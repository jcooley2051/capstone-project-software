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
#define EVENT_BIT_READY_TEMP (1 << 0)
#define EVENT_BIT_READY_LIGHT (1 << 1)
#define EVENT_BIT_READY_PARTICLE (1 << 2)
#define EVENT_BIT_DONE_TEMP (1 << 3)
#define EVENT_BIT_DONE_LIGHT (1 << 4)
#define EVENT_BIT_DONE_PARTICLE (1 << 5)

void sensor_timer_callback(TimerHandle_t xTimer);
void init_timer(void);

#endif