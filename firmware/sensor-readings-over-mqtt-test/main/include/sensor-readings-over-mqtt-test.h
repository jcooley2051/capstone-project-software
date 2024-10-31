#ifndef __SENSOR_READINGS__H__
#define __SENSOR_READINGS__H__

//                      WiFi and MQTT stuff

#define EXAMPLE_MAXIMUM_RETRY 3

void init_flash();
void init_mqtt();
void init_wifi();
void config_wifi();

//                      BME280 stuff

void configure_bme280(void);
void bme_readings_task(void*);
void read_compensation(void);
void print_sensor_readings(uint8_t *readings);


//                      Universal
void init_i2c(void);



void app_main(void);


#endif