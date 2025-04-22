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
#include "adc-battery.h"


// Entry point for firmware //
void app_main(void)
{
// In Production mode, we are connecting to the Wi-Fi and the MQTT broker
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


    // Initialize the I2C bus for the BME280 and VEML7700 and the bus's mutex
    init_i2c();

    // Initialize the ADC to read battery voltage
    init_adc();

// We want to have the BME280 in the following circumstances (SPIN_COATING and BME_SPIN_COATING) or (All 3 stations (breadboard dev mode))
#if (!defined(SPIN_COATING) || defined(BME_SPIN_COATING)) || defined(PHOTOLITHOGRAPHY)
    // Add BME280 temperature and humidity sensor to I2C bus and configure
    add_bme_i2c();
    configure_bme280();
    read_compensation_bme280();
#endif

// Only the photolithography and sputtering stations have light readings
#if defined(PHOTOLITHOGRAPHY) || defined(SPUTTERING)
    // Add VEML7700 light sensor to I2C bus and configure
    add_veml_i2c();
    configure_veml7700();
#endif

// Only the photolithography and spin coating stations have vibration readings
#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)
    init_i2c_adxl();
    // Add ADXL acceleartion sensor to the I2C bus
    add_adxl_i2c();
    configure_adxl();
#endif

// Only spin coating has the IH-PCM-001 sensor
#ifdef SPIN_COATING
    // Initialize the UART peripheral
    init_uart();
#endif

// If we are in PROD_MODE (i.e. connecting to the MQTT broker), then we need to wait for the broker to connect before we start tasks relying on it
#ifdef PROD_MODE
    // Wait to connect to MQTT broker before starting tasks
    xSemaphoreTake(mqtt_semaphore, portMAX_DELAY);
#endif

    // Start timer to manage task synchronization
    init_timer();

// We want to have the BME280 in the following circumstances (SPIN_COATING and BME_SPIN_COATING) or (All 3 stations (breadboard dev mode))
#if (!defined(SPIN_COATING) || defined(BME_SPIN_COATING)) || defined(PHOTOLITHOGRAPHY)
    // Create tasks to take sensor readings and send over MQTT
    xTaskCreate(temp_and_humidity_readings, "Temp/Humidity Readings Task", 8192, NULL, 5, NULL);
#endif

// Only the photolithography and sputtering stations have light readings
#if defined(PHOTOLITHOGRAPHY) || defined(SPUTTERING)
    xTaskCreate(light_readings, "Light Level Readings Task", 8192, NULL, 5, NULL);
#endif

// Only the spin coating station has particle count readings
#ifdef SPIN_COATING
    xTaskCreate(particle_count_readings, "Particle Count Readings Task", 8192, NULL, 5, NULL);
#endif

// Only the photolithography and spin coating stations have vibration readings
#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)
    xTaskCreate(vibration_readings, "Vibration Readings Task", 65536, NULL, 5, NULL);
#endif

// If we are in PROD_MODE, we want to publish readings and battery voltages to the MQTT broker
#ifdef PROD_MODE
    xTaskCreate(mqtt_publish, "MQTT Publishing Task", 65536, NULL, 5, NULL);
    xTaskCreate(publish_battery_readings, "Battery Readings Task", 2048, NULL, 0, NULL);
#endif

// In test mode, simply print the readings to the console
#ifdef TEST_MODE
    xTaskCreate(print_readings, "Readings Printing Task", 65536, NULL, 5, NULL);
    xTaskCreate(print_battery_readings, "Battery Readings Task", 2048, NULL, 0, NULL);
    // Give Sensors time to take initial readings
#endif

    // We want to print the battery readings to the console whether we are in test mode or prod mode
    xTaskCreate(print_battery_readings, "Battery Readings Print Task", 2048, NULL, 0, NULL);

    // Delay to give sensors time to take initial readings
    vTaskDelay(1000 / portTICK_PERIOD_MS);

    // Start timer that synchronizes task triggering
    xTimerStart(sensor_timer, 0);

    while (1) 
    {
        // Pause app_main
        vTaskDelay(portMAX_DELAY);
    }
}
