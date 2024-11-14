#include <stdio.h>
#include "i2c.h"
#include "bme280-temp-sensor.h"


// Entry point for firmware //
void app_main(void)
{
    // Initialize the I2C bus and mutex
    init_i2c();

    // Add BME280 temperature and humidity sensor to I2C bus
    add_bme_i2c();

    // Configure the BME now that it is added to the I2C bus
    configure_bme280();

    // Read the compensation values for the BME280
    read_compensation_bme280();

    //TODO: remove after testing
    temp_and_humidity_t readings;
    while(1)
    {
        get_temp_and_humidity(&readings);
        vTaskDelay(250 / portTICK_PERIOD_MS);  // 250ms delay
    }


}
