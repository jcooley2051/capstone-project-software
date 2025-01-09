#ifndef __PARTICLE_COUNT_SENSOR_PWM__H__
#define __PARTICLE_COUNT_SENSOR_PWM__H__

void app_main(void);
void configure_gpio(void);
void IRAM_ATTR gpio_18_isr(void* arg);

#endif