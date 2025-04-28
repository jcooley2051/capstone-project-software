#include "adc-battery.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_log.h"
#include "esp_err.h"
#include "freertos/FreeRTOS.h"  
#include "config.h"
#include <math.h>

adc_oneshot_unit_handle_t adc1_handle;
adc_cali_handle_t cali_handle;
bool bad_setup = false;

static float smoothed_voltage = -1.0f;



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
            retry_count++;
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
            retry_count++;
            vTaskDelay(ADC_RETRY_DELAY_MS / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < ADC_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("get_battery_voltage", "Error calibrating voltage");
        *voltage_mV = -1000;
        return;
    }

    float raw_voltage = (*voltage_mV) / 1000.0f; // Convert to V
    float alpha = 0.2f;

    if (smoothed_voltage < 0.0f) {
        smoothed_voltage = raw_voltage; // First run init
    } else {
        smoothed_voltage = alpha * raw_voltage + (1.0f - alpha) * smoothed_voltage;
    }

    *voltage_mV = (int)(smoothed_voltage * 1000); // Write back smoothed value in mV
}

/*
 Helper method to convert battery voltage into a percentnage 
*/
void convert_voltage_to_percent(float *percentage, int *voltage_mV)
{
    float voltage_factor = 3.25;
#ifdef PHOTOLITHOGRAPHY
    voltage_factor = BATTERY_VOLTAGE_DIVIDER_FACTOR_PL;
#endif
#ifdef SPIN_COATING
    voltage_factor = BATTERY_VOLTAGE_DIVIDER_FACTOR_SC;
#endif
#ifdef SPUTTERING
    voltage_factor = BATTERY_VOLTAGE_DIVIDER_FACTOR_SP;
#endif

    // Calculate the actual per-cell voltage from the measured value
    float total_voltage = (*voltage_mV / 1000.0f) * voltage_factor; // Convert mV to V
    float per_cell_voltage = total_voltage / 2.0f;

    // Voltage to % mapping for a single cell (from your chart)
    float voltages[] = {
        4.224, 4.186, 4.173, 4.130, 4.103, 4.079, 4.054, 4.034, 4.019, 3.999,
        3.978, 3.958, 3.934, 3.911, 3.890, 3.857, 3.853, 3.830, 3.813, 3.786,
        3.767, 3.731, 3.716, 3.697, 3.677, 3.667, 3.653, 3.638, 3.631, 3.621,
        3.611, 3.600, 3.588, 3.573, 3.569, 3.561, 3.547, 3.538, 3.523, 3.506,
        3.491, 3.464, 3.451, 3.433, 3.395, 3.304, 3.091, 2.970
    };
    float percents[] = {
        100.0, 98.91891892, 97.83783784, 95.67567568, 93.51351351, 91.35135135, 89.18918919,
        87.02702703, 84.86486486, 82.7027027, 80.54054054, 78.37837838, 76.21621622, 74.05405405,
        71.89189189, 69.72972973, 67.56756757, 65.40540541, 63.24324324, 61.08108108, 58.91891892,
        56.21621622, 54.05405405, 51.89189189, 49.72972973, 47.56756757, 45.40540541, 42.7027027,
        40.54054054, 38.37837838, 36.21621622, 33.51351351, 31.35135135, 29.18918919, 27.02702703,
        24.86486486, 22.7027027, 20.54054054, 18.37837838, 16.21621622, 14.05405405, 11.89189189,
        9.72972973, 7.567567568, 5.405405405, 3.243243243, 1.081081081, 0.0
    };

    int len = sizeof(voltages) / sizeof(voltages[0]);

    // Edge cases
    if (per_cell_voltage >= voltages[0]) {
        *percentage = 100.0f;
        return;
    }
    if (per_cell_voltage <= voltages[len - 1]) {
        *percentage = 0.0f;
        return;
    }

    // Interpolation
    for (int i = 0; i < len - 1; i++) {
        if (per_cell_voltage <= voltages[i] && per_cell_voltage >= voltages[i + 1]) {
            float v1 = voltages[i];
            float v2 = voltages[i + 1];
            float p1 = percents[i];
            float p2 = percents[i + 1];

            // Linear interpolation
            *percentage = p1 + (per_cell_voltage - v1) * (p2 - p1) / (v2 - v1);
            // Clamp voltage to [0,100]
            *percentage = fminf(100.0f, fmaxf(0.0f, *percentage));
            return;
        }
    }

    // Fallback
    *percentage = 0.0f;
}