#ifndef BME280_TEMP_SENSOR_H
#define BME280_TEMP_SENSOR_H

// Temperature and humidity to send when there is a sensor error
#define DUMMY_TEMP_READING (-50000)
#define DUMMY_HUMIDITY_READING (150 * 1024)

// Struct to store the temperature and humidity readings from the sensor
typedef struct temp_and_humidity{
    int32_t temp_reading;
    uint32_t humidity_reading;
} temp_and_humidity_t;

/* Configures the sensor settings for the BME280 temperature sensor, must be called before taking readings */
void configure_bme280(void);
/* Reads compensation values from the BME280, used as correction factor for readings, must be called before taking readings */
void read_compensation_bme280(void);
/* take temperature and humidity reading 
    Parameters:
    readings: struct to hold the temperature and humidity readings
*/
void get_temp_and_humidity(temp_and_humidity_t *readings);

#endif