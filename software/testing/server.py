import subprocess
from datetime import datetime
import random
import time

# MQTT configuration
MQTT_BROKER = "test.mosquitto.org"  # Replace with your MQTT broker IP
MQTT_PORT = 1883

# Function definition to send readings to other applications
def publish_to_mqtt(message, topic):
    # Command to publish to MQTT using mosquitto_pub
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,  # Topic for publishing data
        "-m", str(message)  # The message to publish
    ]
    
    # Run the subprocess to publish the message
    subprocess.run(command)

# Loop to create data
while (True):
    data = random.randint(1, 100)
    publish_to_mqtt(data, "/reading/temp")
    time.sleep(1)
    data = random.randint(1,100)
    publish_to_mqtt(data, "/reading/humidity")
    time.sleep(1)
