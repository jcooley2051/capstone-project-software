#ifndef TASKS_H
#define TASKS_H
#include <stdint.h>
#include <stddef.h>

#define ERROR_COUNT_THRESHOLD 10

typedef struct all_readings_t_struct {
    int32_t temp_reading;
    uint32_t humidity_reading;
    float als_reading;
    float white_reading;
    uint16_t particle_count_reading;
    char *vibration_reading;
}all_readings_t;

/* Tasks taking readings and publishing them to the MQTT broker */
void temp_and_humidity_readings(void *arg);
void light_readings(void *arg);
void particle_count_readings(void *arg);
void vibration_readings(void *arg);
void mqtt_publish(void *arg);
void print_readings(void *arg);
void get_message(char *buff, size_t buff_len, all_readings_t *readings);
void print_acceleration(all_readings_t *readings);

#endif