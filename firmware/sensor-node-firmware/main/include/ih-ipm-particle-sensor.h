#ifndef IH_IPM_TEMP_SENSOR_H
#define IH_IPM_TEMP_SENSOR_H

// Particle count reading to send when there is a sensor error
#define DUMMY_PARTICLE_COUNT 0xFFFF
/*
    Take a reading from the particle count sensor
    Parameters:
    reading: Pointer to a uint16 to store the particle count reading
*/
void get_particle_count(uint16_t *reading);

#endif