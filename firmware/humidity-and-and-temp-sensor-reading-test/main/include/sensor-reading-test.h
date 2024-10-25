#ifndef __SENSOR_READING_TEST_H__
#define __SENSOR_READING_TEST_H__

void app_main(void);
void init_i2c(void);
void get_and_print_temp(void);
void get_and_print_temp_async(void);
void get_and_print_humidity(void);
void get_and_print_humidity(void);
void get_and_print_humidity_async(void);
float convert_to_celcius(uint16_t temp_code);
float convert_to_humidity(uint16_t humidity_code);
void temp_task(void);

#endif