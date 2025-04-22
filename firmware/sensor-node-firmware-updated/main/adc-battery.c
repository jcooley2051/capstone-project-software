#include "adc-battery.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_log.h"
#include "esp_err.h"
#include "esp_adc_cal.h"
#include "freertos/FreeRTOS.h"  

adc_oneshot_unit_handle_t adc1_handle;
adc_cali_handle_t cali_handle;
bool bad_setup = false;


void init_adc(void)
{
    // Initialize ADC1 in normal mode
    adc_oneshot_unit_init_cfg_t init_config1 = {
        .unit_id = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };

    esp_err_t ret = ESP_OK;
    int retry_count = 0;

    // Try to init the ADC, retry if needed
    do
    {
        ret = adc_oneshot_new_unit(&init_config1, &adc1_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < ADC_RETRY_COUNT);

    // If ADC failed to init, flag a bad setup
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adc", "Error initializing ADC");
        bad_setup = true;
    }
    
    // Set up the ADC channel we want to read from (channel 9), with default resolution and 12dB attenuation
    adc_oneshot_chan_cfg_t chan_config = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = ADC_ATTEN_DB_12,
    };
    retry_count = 0;
    do
    {
        ret = adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_9, &chan_config); 
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < ADC_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adc", "Error initializing ADC");
        bad_setup = true;
    }

// ESP32S3 supports curve fitting calibration
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    // Init ADC1 Calibration
    adc_cali_curve_fitting_config_t cali_config = {
        .unit_id = ADC_UNIT_1,
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };

    retry_count = 0;
    do
    {
        ret = adc_cali_create_scheme_curve_fitting(&cali_config, &cali_handle); 
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < ADC_RETRY_COUNT);
#endif
// Otherwise use line fitting (ESP32S2)
#if ADC_CALI_SCHEME_LINE_FITTING_SUPPORTED
    adc_cali_line_fitting_config_t cali_config = {
        .unit_id = ADC_UNIT_1,
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };

    retry_count = 0;
    do
    {
        ret = adc_cali_create_scheme_line_fitting(&cali_config, &cali_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < ADC_RETRY_COUNT);
#endif
    if (ret != ESP_OK)
    {
        ESP_LOGE("configure_adc", "Error initializing ADC");
        bad_setup = true;
    }

}

/*
 Read the battery voltage from pin 9 and set voltage_mV to it
*/
void get_battery_voltage(int *voltage_mV)
{
    int voltage_raw;

    // Oneshot read the ADC to get the voltage reading raw
    esp_err_t ret = ESP_OK;
    int retry_count = 0;
    do
    {
        ret = adc_oneshot_read(adc1_handle, ADC_CHANNEL_9, &voltage_raw);
        if (ret != ESP_OK)
        {
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < ADC_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("get_battery_voltage", "Error reading voltage");
        *voltage_mV = -1000;
        return;
    }

    // Use the calibration to convert the raw voltage to mV
    retry_count = 0;
    do
    {
        ret = adc_cali_raw_to_voltage(cali_handle, voltage_raw, voltage_mV);
        if (ret != ESP_OK)
        {
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < ADC_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("get_battery_voltage", "Error calibrating voltage");
        *voltage_mV = -1000;
        return;
    }
}