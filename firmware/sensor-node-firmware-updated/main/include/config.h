#ifndef CONFIG_H
#define CONFIG_H

// Production mode will connect to WiFi and MQTT broker
#define PROD_MODE
// Test mode will print results to console
//#define TEST_MODE

// uncomment which station are we compiling for (uncommenting All stations will enable all sensors)
//#define PHOTOLITHOGRAPHY
//#define SPUTTERING
#define SPIN_COATING

// uncomment if the Spin coating station gets a BME280
//#define BME_SPIN_COATING

#endif