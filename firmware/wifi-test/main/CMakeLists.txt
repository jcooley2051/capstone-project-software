idf_component_register(SRCS "wifi-test.c"
                    INCLUDE_DIRS "." include
                    REQUIRES esp_wifi esp_netif nvs_flash mqtt)
