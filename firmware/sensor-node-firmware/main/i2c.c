#include "esp_log.h"
#include "i2c.h"


// Master bus handle
i2c_master_bus_handle_t bus_handle;

// Sensor device handles
i2c_master_dev_handle_t bme_handle;

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

    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mst_config, &bus_handle));

    // Create the binary semaphore for the I2C mutex
    i2c_mutex = xSemaphoreCreateBinary();
    // Binary semaphores are empty by default
    xSemaphoreGive(i2c_mutex);

    if (i2c_mutex == NULL)
    {
        ESP_LOGE("FreeRTOS", "Failed to initialize i2c mutex. Likely out of heap space");
        // Best chance of fixing this is just to reset the MCU
        abort();
    }
}

// Adds the BME280 as a slave device on the I2C bus
void add_bme_i2c(void)
{
    i2c_device_config_t bme_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BME_I2C_ADDRESS,
        .scl_speed_hz = 100000,
    };

    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &bme_cfg, &bme_handle));
}