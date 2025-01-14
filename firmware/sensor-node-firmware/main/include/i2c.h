#ifndef I2C_H
#define I2C_H

#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#define I2C_CONSOLE_TAG "I2C"

// Clock and Data pins for the I2C bus
#define SCL_GPIO_PIN 6
#define SDA_GPIO_PIN 5

// Automatically select which I2C port to use
#define I2C_PORT_AUTO -1

//Retry any failed transaction up to I2C_TRANSACTION_RETRY_COUNT times
#define I2C_TRANSACTION_RETRY_COUNT 3
// 50 ms delay between transmissions if failure
#define I2C_TRANSMISSION_RETRY_DELAY 50

//Retry any failed transaction up to I2C_SETUP_RETRY_COUNT times
#define I2C_SETUP_RETRY_COUNT 3
// 100 ms delay between setup calls if failure
#define I2C_SETUP_RETRY_DELAY 100

// I2C addresses for each sensor
#define BME_I2C_ADDRESS 0x77
#define VEML_I2C_ADDRESS 0x10

// Clock for BME280, VEML7700 operates at 100kHz
#define I2C_CLOCK_SPEED 100000

// Mutex to protect the I2C bus
extern SemaphoreHandle_t i2c_mutex;

// Define handles as Extern so they can be accessed within the sensor files
extern i2c_master_bus_handle_t bus_handle;
extern i2c_master_dev_handle_t bme_handle;
extern i2c_master_dev_handle_t veml_handle;

// Initialize the I2C bus
void init_i2c(void);

// Add the BME280 temperature and humidity sensor as a device on the I2C bus
void add_bme_i2c(void);

// Add the VEML7700 ambient light sensor as a device on the I2C bus
void add_veml_i2c(void);

#endif