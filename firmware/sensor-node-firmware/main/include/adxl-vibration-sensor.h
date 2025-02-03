#ifndef ADXL_VIBRATION_SENSOR_H
#define ADXL_VIBRATION_SENSOR_H

#define ADXL_READING_SIZE_BYTES 9
#define ADXL_SAMPLE_RATE 500 // Hz
#define ADXL_NUM_READINGS ADXL_SAMPLE_RATE

#define ADXL_DUMMY_VALUE 0xFF

void configure_adxl(void);
void get_vibration_readings(uint8_t *readings);
void encode_to_hex(uint8_t *readings_buffer, size_t buffer_length, char *output_buffer);

#endif