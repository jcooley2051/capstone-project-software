#ifndef TASKS_H
#define TASKS_H

#define ERROR_COUNT_THRESHOLD 10

void temp_and_humidity_readings(void *arg);
void light_readings(void *arg);
void particle_count_readings(void *arg);
void mqtt_publish(void *arg);

#endif