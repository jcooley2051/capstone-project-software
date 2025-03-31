#ifndef ADC_BATTERY_H
#define ADC_BATTERY_H

#define ADC_RETRY_COUNT 3
#define ADC_RETRY_DELAY_MS 50

void init_adc(void);
void get_battery_voltage(int *voltage);

#endif