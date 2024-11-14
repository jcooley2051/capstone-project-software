import subprocess
import json
from datetime import datetime
from threading import Thread, Lock

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1337

# Dictionary to store temperature and humidity data
data = {"temp": None, "humidity": None, "time": None}

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

def listen_to_topic(topic, key):
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
            for line in proc.stdout:
                line = line.strip()
                
                try:
                    # Update the corresponding key in the dictionary
                    with data_lock:  # Use the lock to ensure thread safety
                        data[key] = float(line)
                        data["time"] = datetime.now()  # Update the timestamp

                    # Check if both temperature and humidity are updated
                    with data_lock:
                        if data["temp"] is not None and data["humidity"] is not None:
                            # Print the temperature in Celsius and humidity
                            # print(f"Temperature: {data['temp']}°C, Humidity: {data['humidity']}%, Time: {data['time'].strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Prepare the data to be published
                            message = {
                                "temp": data["temp"],
                                "humidity": data["humidity"],
                                "time": data["time"].strftime('%Y-%m-%d %H:%M:%S')
                            }

                            # Publish the data to MQTT
                            publish_to_mqtt(message)
                            
                            # Reset data for next reading
                            data["temp"], data["humidity"] = None, None

                except ValueError:
                    print(f"Invalid data received on topic '{topic}': {line}")

    except Exception as e:
        print(f"Error in listening to topic {topic}: {e}")

# Create threads to listen to each topic
temperature_thread = Thread(target=listen_to_topic, args=("reading/temp", "temp"))
humidity_thread = Thread(target=listen_to_topic, args=("reading/humidity", "humidity"))

# Start both threads
temperature_thread.start()
humidity_thread.start()

# Wait for both threads to finish
temperature_thread.join()
humidity_thread.join()