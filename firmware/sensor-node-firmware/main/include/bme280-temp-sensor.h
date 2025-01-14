#ifndef BME280_TEMP_SENSOR_H
#define BME280_TEMP_SENSOR_H

#define DUMMY_TEMP_READING (-50000)
#define DUMMY_HUMIDITY_READING (150 * 1024)


typedef struct temp_and_humidity{
    int32_t temp_reading;
    uint32_t humidity_reading;
} temp_and_humidity_t;

void configure_bme280(void);
void read_compensation_bme280(void);
void get_temp_and_humidity(temp_and_humidity_t *readings);

#endif