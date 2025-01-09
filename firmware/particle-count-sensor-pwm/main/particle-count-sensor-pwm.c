#include <stdio.h>
#include "FreeRTOS/FreeRTOS.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "esp_timer.h"

#define PWM_INPUT_GPIO 18

static uint64_t rising_edge_time = 0;
static uint64_t falling_edge_time = 0;
static uint64_t pulse_width = 0;

// This function might be a bit long for an ISR
void IRAM_ATTR gpio_18_isr(void* arg) {
    static int last_level = 0;
    int current_level = gpio_get_level(PWM_INPUT_GPIO);

    uint64_t current_time = esp_timer_get_time(); // Get current time in microseconds

    if (current_level == 1 && last_level == 0) {
        // Rising edge detected
        rising_edge_time = current_time;
    } 
    else if (current_level == 0 && last_level == 1) {
        // Falling edge detected
        falling_edge_time = current_time;
    }

    last_level = current_level; // Update last level
}


void configure_gpio(void){
    gpio_config_t config = {
        .pin_bit_mask = (1ULL << 18),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_ANYEDGE,
    };
    ESP_ERROR_CHECK(gpio_config(&config)); 
    ESP_ERROR_CHECK(gpio_install_isr_service(0));
    ESP_ERROR_CHECK(gpio_isr_handler_add(GPIO_NUM_18, gpio_18_isr, NULL));
}

void reading_task(void* arg){
    while(1){
        ESP_LOGI("Task", "In the readings Task");
        pulse_width = falling_edge_time - rising_edge_time; // Calculate pulse width
        printf("Concentration: %0.2f ug/m^3", (float)pulse_width/1000);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}


void app_main(void) {
    configure_gpio();
    printf("Waiting for PWM signal...\n");
    xTaskCreate(reading_task, "Particle Count Readings Task", 2048, NULL, 5, NULL);
}
