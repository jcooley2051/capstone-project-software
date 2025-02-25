#ifndef TASKS_H
#define TASKS_H

#define ERROR_COUNT_THRESHOLD 10

/* Tasks taking readings and publishing them to the MQTT broker */
void temp_and_humidity_readings(void *arg);
void light_readings(void *arg);
void particle_count_readings(void *arg);
void vibration_readings(void *arg);
void print_readings_uptime(void *arg);

#endif