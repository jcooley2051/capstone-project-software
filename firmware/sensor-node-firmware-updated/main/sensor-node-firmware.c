#include "config.h"
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
#ifdef PROD_MODE
    // Initialize the NVS for WiFi credential flash storage
    init_flash();

    // Initialize WiFi driver and event handling
    init_wifi();

    // Configure WiFi settings and connect to network
    config_wifi();

    // Wait for the WiFi driver to start and connect to a network before starting MQTT broker
    xSemaphoreTake(wifi_semaphore, portMAX_DELAY);

    // Initialize MQTT and connect to broker
    init_mqtt();
#endif
    // Initialize the I2C buses and mutexes
    init_i2c();

    // Add BME280 temperature and humidity sensor to I2C bus and configure
    add_bme_i2c();
    configure_bme280();
    read_compensation_bme280();

#if defined(PHOTOLITHOGRAPHY) || defined(SPUTTERING)
    // Add VEML7700 light sensor to I2C bus and configure
    add_veml_i2c();
    configure_veml7700();
#endif
#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)
    init_i2c_adxl();
    // Add ADXL acceleartion sensor to the I2C bus
    add_adxl_i2c();
    configure_adxl();
#endif

#ifdef SPIN_COATING
    // Initialize the UART peripheral
    init_uart();
#endif

#ifdef PROD_MODE
    // Wait to connect to MQTT broker before starting tasks
    xSemaphoreTake(mqtt_semaphore, portMAX_DELAY);
#endif
    // Start timer to manage task synchronization
    init_timer();

    // Create tasks to take sensor readings and send over MQTT
    xTaskCreate(temp_and_humidity_readings, "Temp/Humidity Readings Task", 8192, NULL, 5, NULL);
#if defined(PHOTOLITHOGRAPHY) || defined(SPUTTERING)
    xTaskCreate(light_readings, "Light Level Readings Task", 8192, NULL, 5, NULL);
#endif
#ifdef SPIN_COATING
    xTaskCreate(particle_count_readings, "Particle Count Readings Task", 8192, NULL, 5, NULL);
#endif
#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)
    xTaskCreate(vibration_readings, "Vibration Readings Task", 65536, NULL, 5, NULL);
#endif
#ifdef PROD_MODE
    xTaskCreate(mqtt_publish, "MQTT Publishing Task", 65536, NULL, 5, NULL);
#endif
#ifdef TEST_MODE
    xTaskCreate(print_readings, "Readings Printing Task", 65536, NULL, 5, NULL);
#endif

    // Start timer for tasks
    xTimerStart(sensor_timer, 0);

    while (1) 
    {
        // Pause app_main
        vTaskDelay(portMAX_DELAY);
    }
}
