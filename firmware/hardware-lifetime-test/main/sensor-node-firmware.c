#include <stdio.h>
#include "i2c.h"
#include "uart.h"
#include "wifi.h"
#include "bme280-temp-sensor.h"
#include "veml7700-light-sensor.h"
#include "adxl-vibration-sensor.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "mqtt.h"
#include "timer.h"
#include "tasks.h"


// Entry point for firmware //
void app_main(void)
{

    // Initialize the I2C buses and mutexes
    init_i2c();

    // Add BME280 temperature and humidity sensor to I2C bus and configure
    add_bme_i2c();
    configure_bme280();
    read_compensation_bme280();

    // Add VEML7700 light sensor to I2C bus and configure
    add_veml_i2c();
    configure_veml7700();

    // Add ADXL acceleartion sensor to the I2C bus
    add_adxl_i2c();
    configure_adxl();

    // Initialize the UART peripheral
    init_uart();

    // Start timer to manage task synchronization
    init_timer();

    // Create tasks to take sensor readings and send over MQTT
    xTaskCreate(temp_and_humidity_readings, "Temp/Humidity Readings Task", 8192, NULL, 5, NULL);
    xTaskCreate(light_readings, "Light Level Readings Task", 8192, NULL, 5, NULL);
    xTaskCreate(particle_count_readings, "Particle Count Readings Task", 8192, NULL, 5, NULL);
    xTaskCreate(vibration_readings, "Vibration Readings Task", 65536, NULL, 5, NULL);
    xTaskCreate(print_readings_uptime, "Vibration Readings Task", 65536, NULL, 5, NULL);

    // Start timer for tasks
    xTimerStart(sensor_timer, 0);

    while (1) 
    {
        // Pause app_main
        vTaskDelay(portMAX_DELAY);
    }
}
