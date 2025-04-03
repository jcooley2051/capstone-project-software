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
#MQTT_PORT = 1883

# Dictionary to store data for three nodes
PL_data = {"temperature": None, "humidity": None, "ambient_light":None, "vibration":None}
SC_data = {"temperature":None, "humidity":None, "particle_count":None, "vibration":None}
SP_data = {"temperature":None, "humidity": None, "ambient_light":None}
data = {"PL_data": PL_data, "SC_data": SC_data, "SP_data": SP_data, "time": None}

# Lock to ensure thread-safe updates to the data dictionary
data_lock = Lock()

# Publish data over MQTT
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
# Used for processing acceleration data
def parse_hex_string(hex_string):
    hex_string = re.sub(r'[^0-9A-Fa-f]', '', hex_string)
    return [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)]

# Determine sign of readings
# Used for processing acceleration data
def convert_to_signed_20bit(value):
    if value & 0x80000:
        value -= 0x100000
    return value

# Convert readings from hex to decimal
# Used for processing acceleration data
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

# Filter out acceleration due to gravity
# Used for processing acceleration data
def high_pass_filter(accel_data, cutoff=1, fs=500):
    b, a = signal.butter(1, cutoff / (fs / 2), btype='high', analog=False)
    return signal.filtfilt(b, a, accel_data, axis=0)

# Integrate acceleration readings to get displacement
# Used for processing acceleration data
def integrate(accel_data, dt=0.002):
    velocity = np.cumsum(accel_data * dt, axis=0)
    displacement = np.cumsum(velocity * dt, axis=0)
    return velocity, displacement

# Process acceleration data
def process_acceleration(temp_buffer):
    # Convert hex string to decimal
    buffer_bytes = parse_hex_string(temp_buffer)
    accel_data = decode_sensor_readings(buffer_bytes)
    filtered_accel = high_pass_filter(accel_data)
    
    # Find average acceleration in each direction
    accel_x_avg = np.max(filtered_accel[:, 0])  # Average of x-component
    accel_y_avg = np.max(filtered_accel[:, 1])  # Average of y-component
    accel_z_avg = np.max(filtered_accel[:, 2])  # Average of z-component

    # Compute net magnitude of acceleration (m/s^2)
    accel_magnitude = np.sqrt(accel_x_avg**2 + accel_y_avg**2 + accel_z_avg**2)
    return round(accel_magnitude, 2)

# Check for remaining null values in data dictionary
def check_null(data):
    for key, value in data.items():
        if key == "time":  # Skip checking "time"
            continue
        if isinstance(value, dict):  # If the value is a dictionary, check its values
            if any(v is None for v in value.values()):
                return True
    return False

# Continuously process readings from ESP32 and send to data analysis
def listen_to_topic(topic, key):
    while True:
        print(f"Listening to topic: {topic}")  # Check for MQTT connection on system startup
        
        command = [
            "mosquitto_sub",
            "-h", MQTT_BROKER,
            "-p", str(MQTT_PORT),
            "-t", topic
        ]

        try:
            with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
                # Read in lines over MQTT
                for line in proc.stdout:
                    line = line.strip()

                    # Skip empty lines
                    if not line:
                        continue 

                    # Check which thread received data and update corresponding embedded dictionary
                    with data_lock:  # Use the lock to ensure thread safety
                        if key == "PL_thread":
                            new_data = json.loads(line)
                            data["PL_data"] = {key: new_data[key] if key in new_data else data["PL_data"][key] for key in data["PL_data"]}
                            if all(char == 'F' for char in data["PL_data"]["vibration"]): # Check for acceleration error
                                data["PL_data"]["vibration"] = -1
                            else:
                                data["PL_data"]["vibration"] = process_acceleration(data["PL_data"]["vibration"]) # Process acceleration
                        elif key == "SC_thread":
                            new_data = json.loads(line)
                            data["SC_data"] = {key: new_data[key] if key in new_data else data["SC_data"][key] for key in data["SC_data"]}
                            if all(char == 'F' for char in data["SC_data"]["vibration"]): # Check for acceleration error
                                data["SC_data"]["vibration"] = -1
                            else:
                                data["SC_data"]["vibration"] = process_acceleration(data["SC_data"]["vibration"]) # Process acceleration
                        elif key == "SP_thread":
                            new_data = json.loads(line)
                            data["SP_data"] = {key: new_data[key] if key in new_data else data["SP_data"][key] for key in data["SP_data"]}

                        # Check if all threads have updated data
                        if not check_null(data):  
                            data["time"] = datetime.now().replace(microsecond=0).isoformat()  # Update the timestamp
                           
                            # Publish the data to MQTT
                            publish_to_mqtt(data)
                                
                            # Reset data for next reading
                            data["PL_data"] = {"temperature": None, "humidity": None, "ambient_light": None, "vibration": None}
                            data["SC_data"] = {"temperature": None, "humidity": None, "particle_count": None, "vibration": None}
                            data["SP_data"] = {"temperature": None, "humidity": None, "ambient_light": None}
                            data["time"] = None

        except Exception as e:
            print(f"Error in listening to topic {topic}: {e}")

            # Wait five seconds then try to reconnect
            time.sleep(5)

# Create threads to listen to each node
PL_thread = Thread(target=listen_to_topic, args=("topic/PL", "PL_thread"), daemon=True)
SC_thread = Thread(target=listen_to_topic, args=("topic/SC", "SC_thread"), daemon=True)
SP_thread = Thread(target=listen_to_topic, args=("topic/SP", "SP_thread"), daemon=True)

# Start both threads
PL_thread.start()
SC_thread.start()
SP_thread.start()

# Wait for both threads to finish
# For syntax only, threads loop continuously
PL_thread.join()
SC_thread.join()
SP_thread.join()
