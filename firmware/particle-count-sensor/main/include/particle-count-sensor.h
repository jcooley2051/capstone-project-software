#ifndef __PARTICLE_COUNT__H__
#define __PARTICLE_COUNT__H__

void app_main(void);
void init_i2c(void);
void configure_sensor(void);
void sensor_readings_task(void*);
void print_sensor_reading(uint8_t*);


#endif
