#ifndef VEML7700_LIGHT_SENSOR_H
#define VEML7700_LIGHT_SENSOR_H

// Used in conversion for sensor reading to LUX
#define RESOLUTION 0.0144f
// Dummy value sent when there is an issue with reading the sensor
#define DUMMY_LIGHT_READING (-1000)
// Structure to hold the sensor readings for both the absolute and white light sensor
typedef struct light_readings {
    float als_reading;
    float white_reading;
} light_readings_t;

/* Configures the VEML ambient light sensor to take readings, must be called before taking readings*/
void configure_veml7700(void);
/* Gets light level readings from the ambient light sensor
    Parameters:
    readings: pointer to a struct to hold the ambient light sensor readings
*/
void get_light_level(light_readings_t *readings);

#endif