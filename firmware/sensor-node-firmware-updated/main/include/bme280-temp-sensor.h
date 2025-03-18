#ifndef BME280_TEMP_SENSOR_H
#define BME280_TEMP_SENSOR_H

// Configuration register definitions
#define BME_CONFIG_REGISTER 0xF5
#define BME_CTRL_MEAS_REGISTER 0xF4
#define BME_CTRL_HUM_REGISTER 0xF2
// Compensation register definitions
#define DIG_T1_REGISTER 0x88
#define DIG_T2_REGISTER 0x8A
#define DIG_T3_REGISTER 0x8C
#define DIG_H1_REGISTER 0xA1
#define DIG_H2_REGISTER 0xE1
#define DIG_H3_REGISTER 0xE3
#define DIG_H4_REGISTER 0xE4
#define DIG_H5_REGISTER 0xE5
#define DIG_H6_REGISTER 0xE7
// Readings register definition
#define BME_READINGS_REGISTER 0xF7

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