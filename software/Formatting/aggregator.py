import subprocess
import json
import time
from datetime import datetime
from threading import Thread, Lock
import numpy as np
import scipy.signal as signal
import re

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1337

# Local testing configuration
#MQTT_BROKER = "test.mosquitto.org"

# Dictionary to store temperature and humidity data
data = {"temperature": None, "humidity": None, "ambient_light":None, "particle_count":None, "vibration":None, "time": None}

# Lock to ensure thread-safe updates to the data dictionary
data_lock = Lock()

# Function to publish data over MQTT
def publish_to_mqtt(message):
    """Publish the message to the specified MQTT topic."""
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", "reading/formatted",
        "-m", json.dumps(message)  # Publish as a JSON string
    ]
    subprocess.run(command)

# Remove any null characters from hex string
def parse_hex_string(hex_string):
    hex_string = re.sub(r'[^0-9A-Fa-f]', '', hex_string)
    return [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)]

# Determine sign of readings
def convert_to_signed_20bit(value):
    if value & 0x80000:
        value -= 0x100000
    return value

# Convert readings from hex to decimal
def decode_sensor_readings(read_buffer):
    num_readings = len(read_buffer) // 9
    accel_data = []
    
    for i in range(num_readings):
        start = i * 9
        x_data = (read_buffer[start] << 12) | (read_buffer[start + 1] << 4) | (read_buffer[start + 2] >> 4)
        y_data = (read_buffer[start + 3] << 12) | (read_buffer[start + 4] << 4) | (read_buffer[start + 5] >> 4)
        z_data = (read_buffer[start + 6] << 12) | (read_buffer[start + 7] << 4) | (read_buffer[start + 8] >> 4)
        
        x_data = convert_to_signed_20bit(x_data)
        y_data = convert_to_signed_20bit(y_data)
        z_data = convert_to_signed_20bit(z_data)
        
        accel_x = (x_data / 256000) * 9.81
        accel_y = (y_data / 256000) * 9.81
        accel_z = (z_data / 256000) * 9.81
        
        accel_data.append([accel_x, accel_y, accel_z])
    
    return np.array(accel_data)

# High pass filter to remove acceleration due to gravity in readings
def high_pass_filter(accel_data, cutoff=1, fs=500):
    b, a = signal.butter(1, cutoff / (fs / 2), btype='high', analog=False)
    return signal.filtfilt(b, a, accel_data, axis=0)

# Integrate acceleration readings to get displacement
def integrate(accel_data, dt=0.002):
    velocity = np.cumsum(accel_data * dt, axis=0)
    displacement = np.cumsum(velocity * dt, axis=0)
    return velocity, displacement

# Take raw acceleration data and call required functions to get average displacement
def process_acceleration(temp_buffer):
    buffer_bytes = parse_hex_string(temp_buffer)
    accel_data = decode_sensor_readings(buffer_bytes)
    filtered_accel = high_pass_filter(accel_data)
    velocity, displacement = integrate(filtered_accel)
    averages = np.mean(displacement, axis=0)
    return averages.tolist()

def listen_to_topic(topic, key):
    while True:
        """Function to listen to a specific MQTT topic and update the data dictionary."""
        print(f"Listening to topic: {topic}")  # Debugging statement to check if the function is called
        
        command = [
            "mosquitto_sub",
            "-h", MQTT_BROKER,
            "-p", str(MQTT_PORT),
            "-t", topic
        ]

        try:
            with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
                # Read in lines from MQTT
                for line in proc.stdout:
                    line = line.strip()

                    # Skip empty lines
                    if not line:
                        continue 

                    # Update dictionary keys
                    with data_lock:  # Use the lock to ensure thread safety
                        data.update(json.loads(line))
                        data["vibration"] = process_acceleration(data["vibration"]) # Convert acceleration to displacement
                        data["time"] = datetime.now().isoformat()  # Update the timestamp

                        if data["temperature"] is not None and data["humidity"] is not None and data["ambient_light"] is not None and data["particle_count"] is not None and data["vibration"] is not None:     
                            # Prepare the data to be published
                            message = {
                                "temperature": data["temperature"],
                                "humidity": data["humidity"],
                                "ambient_light": data["ambient_light"],
                                "particle_count": data["particle_count"],
                                "vibration": data["vibration"],
                                "time": data["time"]
                            }

                            # Publish the data to MQTT
                            publish_to_mqtt(message)
                                
                            # Reset data for next reading
                            data["temperature"], data["humidity"], data["ambient_light"], data["particle_count"], data["vibration"] = None, None, None, None, None

        except Exception as e:
            print(f"Error in listening to topic {topic}: {e}")

            # Wait five seconds then try to reconnect
            time.sleep(5)

# Create threads to listen to each node
node1_thread = Thread(target=listen_to_topic, args=("topic/test", "node1"))

# Start both threads
node1_thread.start()

# Wait for both threads to finish
node1_thread.join()
