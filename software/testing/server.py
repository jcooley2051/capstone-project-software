import subprocess
from datetime import datetime
import time

# MQTT configuration
MQTT_BROKER = "test.mosquitto.org"  # Online test broker
MQTT_PORT = 1337

# Function to send readings
def publish_to_mqtt(message, topic):
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,
        "-m", str(message)
    ]
    subprocess.run(command)

# Loop to publish each line in file
with open("/Users/madisonharr/Desktop/full-system-recording.txt", "r") as file: # Change file path when using
    while True:
        for line in file:
            publish_to_mqtt(line, "topic/test")
            time.sleep(1)
