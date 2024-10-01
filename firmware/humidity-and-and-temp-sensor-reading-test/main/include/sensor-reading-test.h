#ifndef __SENSOR_READING_TEST_H__
#define __SENSOR_READING_TEST_H__

void app_main(void);
void init_i2c(void);
void get_and_print_temp(void);
float convert_to_celcius(uint16_t temp_code);
void temp_task(void);

#endif