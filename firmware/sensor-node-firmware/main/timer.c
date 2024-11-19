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

    // Create the timer with 250ms interval
    sensor_timer = xTimerCreate("Sensor Timer", pdMS_TO_TICKS(250), pdTRUE, 0, sensor_timer_callback);
}


void sensor_timer_callback(TimerHandle_t xTimer) 
{
    // Set bits to notify sensor reading tasks
    xEventGroupSetBits(sensor_event_group, SENSOR_EVENT_BIT_0 | SENSOR_EVENT_BIT_1);
}