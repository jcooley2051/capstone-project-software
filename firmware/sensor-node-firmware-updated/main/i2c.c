#include "config.h"
#include "esp_log.h"
#include "i2c.h"


// Master bus handles
i2c_master_bus_handle_t bus_handle;
i2c_master_bus_handle_t adxl_bus_handle;

// Sensor device handles
i2c_master_dev_handle_t bme_handle;
i2c_master_dev_handle_t veml_handle;
i2c_master_dev_handle_t adxl_handle;

// Mutex for resource protection
SemaphoreHandle_t i2c_mutex;
SemaphoreHandle_t adxl_i2c_mutex;


// Initialize the I2C master bus
void init_i2c(void)
{
    // Master bus config for the bus with the BME and VEML sensors
    i2c_master_bus_config_t i2c_mst_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_PORT_AUTO,
        .scl_io_num = SCL_GPIO_PIN,
        .sda_io_num = SDA_GPIO_PIN,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };  

    // Create the master bus for the BME and the VEML sensors
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
        ESP_LOGE("init_i2c", "Failed to create i2c master bus");
        abort();
    }

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
        ESP_LOGE("init_i2c", "Failed to initialize i2c mutex. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }
    
    if (xSemaphoreGive(i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("init_i2c", "Failed to give i2c mutex");
        abort();
    }
}

#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)
void init_i2c_adxl(void)
{
    // Master bus config for the bus with the ADXL sensor
    i2c_master_bus_config_t adxl_i2c_mst_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_PORT_AUTO,
        .scl_io_num = ADXL_SCL_GPIO_PIN,
        .sda_io_num = ADXL_SDA_GPIO_PIN,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };  

    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    // Create the master bus for the ADXL sensor
    retry_count = 0;
    do
    {
        ret = i2c_new_master_bus(&adxl_i2c_mst_config, &adxl_bus_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("init_i2c", "Failed to create adxl i2c master bus");
        abort();
    }

    // Create the binary semaphore for the ADXL's I2C mutex
    do
    {
        adxl_i2c_mutex = xSemaphoreCreateBinary();
        retry_count++;
        if (i2c_mutex == NULL)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while(adxl_i2c_mutex == NULL && retry_count < I2C_SETUP_RETRY_COUNT);

    if (adxl_i2c_mutex == NULL)
    {
        ESP_LOGE("init_i2c", "Failed to initialize i2c mutex. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }

    if (xSemaphoreGive(adxl_i2c_mutex) != pdTRUE)
    {
        ESP_LOGE("init_i2c_adxl", "Failed to give adxl i2c mutex");
        abort();
    }
}
#endif

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
        ESP_LOGE("add_bme_i2c", "Failed to add BME280 to I2C bus");
        abort();
    }
}

#if defined(PHOTOLITHOGRAPHY) || defined(SPUTTERING)
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
        ESP_LOGE("add_veml_i2c", "Failed to add VEML7700 to I2C bus");
        abort();
    }
}
#endif

#if defined(PHOTOLITHOGRAPHY) || defined(SPIN_COATING)
void add_adxl_i2c(void)
{
    i2c_device_config_t adxl_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = ADXL_I2C_ADDRESS,
        .scl_speed_hz = ADXL_I2C_CLOCK_SPEED,
    };

    int retry_count = 0;
    esp_err_t ret = ESP_OK;
    
    do
    {
        ret = i2c_master_bus_add_device(adxl_bus_handle, &adxl_cfg, &adxl_handle);
        retry_count++;
        if (ret != ESP_OK)
        {
            vTaskDelay(I2C_SETUP_RETRY_DELAY / portTICK_PERIOD_MS);
        }
    } while (ret != ESP_OK && retry_count < I2C_SETUP_RETRY_COUNT);

    if (ret != ESP_OK)
    {
        ESP_LOGE("add_adxl_i2c", "Failed to add ADXL to I2C bus");
        abort();
    }
}
#endif