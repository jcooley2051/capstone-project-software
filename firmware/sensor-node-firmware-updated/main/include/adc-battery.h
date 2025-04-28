#ifndef ADC_BATTERY_H
#define ADC_BATTERY_H

#define ADC_RETRY_COUNT 3
#define ADC_RETRY_DELAY_MS 50

// Voltage divisers may have slightly different ratios between different boards
#define BATTERY_VOLTAGE_DIVIDER_FACTOR_PL 3.255f 
#define BATTERY_VOLTAGE_DIVIDER_FACTOR_SC 3.255f 
#define BATTERY_VOLTAGE_DIVIDER_FACTOR_SP 3.255f 

void init_adc(void);
void get_battery_voltage(int *voltage);
void convert_voltage_to_percent(float *percentage, int *voltage_mV);

#endif