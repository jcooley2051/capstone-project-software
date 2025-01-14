#ifndef VEML7700_LIGHT_SENSOR_H
#define VEML7700_LIGHT_SENSOR_H

#define RESOLUTION 0.0168f
#define DUMMY_LIGHT_READING (-1000)

typedef struct light_readings {
    float als_reading;
    float white_reading;
} light_readings_t;

void configure_veml7700(void);
void get_light_level(light_readings_t *readings);

#endif