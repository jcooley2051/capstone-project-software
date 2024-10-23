#ifndef __BME280__H__
#define __BME280__H__

void app_main(void);
void init_i2c(void);
void configure_bme280(void);
void bme_readings_task(void*);
void read_compensation(void);

void print_sensor_readings(uint8_t *readings);

#endif