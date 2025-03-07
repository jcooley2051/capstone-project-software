#include "config.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/timers.h"
#include "timer.h"


EventGroupHandle_t sensor_event_group;
TimerHandle_t sensor_timer;


void init_timer(void)
{
    // Create the event group
    sensor_event_group = xEventGroupCreate();

    // Create the timer
    sensor_timer = xTimerCreate("Sensor Timer", pdMS_TO_TICKS(UPDATE_PERIOD_MS), pdTRUE, 0, sensor_timer_callback);
}


void sensor_timer_callback(TimerHandle_t xTimer) 
{
    // Set bits to notify sensor reading tasks that they should take another reading
    xEventGroupSetBits(sensor_event_group, EVENT_BIT_READY_TEMP | EVENT_BIT_READY_LIGHT | EVENT_BIT_READY_PARTICLE);
}