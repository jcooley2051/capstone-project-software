#include "esp_log.h"
#include "i2c.h"


// Master bus handle
i2c_master_bus_handle_t bus_handle;

// Sensor device handles
i2c_master_dev_handle_t bme_handle;
i2c_master_dev_handle_t veml_handle;

// Mutex for resource protection
SemaphoreHandle_t i2c_mutex;


// Initialize the I2C master bus
void init_i2c(void)
{

    i2c_master_bus_config_t i2c_mst_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_PORT_AUTO,
        .scl_io_num = SCL_GPIO_PIN,
        .sda_io_num = SDA_GPIO_PIN,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };  
    int retry_count = 0;
    esp_err_t ret = ESP_OK;

    do
    {
        ret = i2c_new_master_bus(&i2c_mst_config, &bus_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE(I2C_CONSOLE_TAG, "Failed to create i2c master bus");
        abort();
    }

    retry_count = 0;

    // Create the binary semaphore for the I2C mutex
    do
    {
        i2c_mutex = xSemaphoreCreateBinary();
        retry_count++;
        if (i2c_mutex == NULL)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(i2c_mutex == NULL && retry_count < I2C_SETUP_RETRY_COUNT);

    if (i2c_mutex == NULL)
    {
        ESP_LOGE("FreeRTOS", "Failed to initialize i2c mutex. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }

    
    // Binary semaphores are zero by default, there is no risk of failure in this action
    xSemaphoreGive(i2c_mutex);

}

// Adds the BME280 as a slave device on the I2C bus
void add_bme_i2c(void)
{
    i2c_device_config_t bme_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BME_I2C_ADDRESS,
        .scl_speed_hz = I2C_CLOCK_SPEED,
    };

    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    
    do
    {
        ret = i2c_master_bus_add_device(bus_handle, &bme_cfg, &bme_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE(I2C_CONSOLE_TAG, "Failed to add BME280 to I2C bus");
        abort();
    }
}

// Adds the VEML7700 as a slave device on the I2C bus
void add_veml_i2c(void)
{
    i2c_device_config_t veml_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = VEML_I2C_ADDRESS,
        .scl_speed_hz = I2C_CLOCK_SPEED,
    };

    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    
    do
    {
        ret = i2c_master_bus_add_device(bus_handle, &veml_cfg, &veml_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE(I2C_CONSOLE_TAG, "Failed to add VEML7700 to I2C bus");
        abort();
    }
}