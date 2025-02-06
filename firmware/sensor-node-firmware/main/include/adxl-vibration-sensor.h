#ifndef ADXL_VIBRATION_SENSOR_H
#define ADXL_VIBRATION_SENSOR_H

#define ADXL_READING_SIZE_BYTES 9
#define ADXL_SAMPLE_RATE 500 // Hz
#define ADXL_NUM_READINGS ADXL_SAMPLE_RATE / 2

#define ADXL_DUMMY_VALUE 0xFF

/* Configures sensor settings for the ADXL vibration sensor, must be called before readings are taken */
void configure_adxl(void);
/* Takes readings from the vibration sensor.
    Parameters:
    readings: a buffer to store the acceleration readings, must be of size ADXL_READING_SIZE_BYTES * ADXL_SAMPLE_RATE
*/
void get_vibration_readings(uint8_t *readings);
/* Takes in a buffer of acceleration readings and converts them into a hex string
    Parameters:
    readings_buffer: a pointer to a buffer of bytes to convert into hex
    buffer_length: the length of the readings_buffer array
    output_buffer: a character array to store the hex string in, must be of size buffer_length * 2 + 1
*/
void encode_to_hex(uint8_t *readings_buffer, size_t buffer_length, char *output_buffer);

#endif