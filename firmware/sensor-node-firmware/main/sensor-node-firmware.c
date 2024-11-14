#include <stdio.h>
#include "i2c.h"
#include "bme280-temp-sensor.h"
#include "veml7700-light-sensor.h"


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

    // Add VEML7700 light sensor to I2C bus
    add_veml_i2c();

    // Configure the VEML now that it is added to the I2C bus
    configure_veml7700();

    //TODO: remove after testing
    temp_and_humidity_t bne_readings;
    light_readings_t veml_readings;
    while(1)
    {
        get_temp_and_humidity(&bne_readings);
        get_light_level(&veml_readings);
        vTaskDelay(250 / portTICK_PERIOD_MS);  // 250ms delay
    }


}
