#ifndef __VEML7700__H__
#define __VEMO7700__H__

void app_main(void);
void init_i2c(void);
void configure_veml7700(void);
void veml_readings_task(void*);
void print_sensor_reading(uint8_t*);
void encode_to_hex(const uint8_t *buffer, size_t buffer_len, char *output);

#endif