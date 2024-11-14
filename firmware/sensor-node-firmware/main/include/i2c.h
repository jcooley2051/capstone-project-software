#ifndef I2C_H
#define I2C_H

#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5
#define I2C_PORT_AUTO -1

#define BME_I2C_ADDRESS 0x77

// Mutex to protect the I2C bus
extern SemaphoreHandle_t i2c_mutex;

// Define handles as Extern so they can be accessed within the sensor files
extern i2c_master_bus_handle_t bus_handle;
extern i2c_master_dev_handle_t bme_handle;

void init_i2c(void);
void add_bme_i2c(void);

#endif