import subprocess
import json
import time
from datetime import datetime
from threading import Thread, Lock

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1337

# Dictionary to store temperature and humidity data
data = {"temperature": None, "humidity": None, "ambient_light":None, "particle_count":None, "time": None}

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
                for line in proc.stdout:
                    line = line.strip()
                    
                    try:
                        # Update the corresponding key in the dictionary
                        with data_lock:  # Use the lock to ensure thread safety
                            data = json.loads(line)
                            data["time"] = datetime.now().isoformat()  # Update the timestamp

                        # Check if both temperature and humidity are updated
                        with data_lock:
                            if data["temperature"] is not None and data["humidity"] is not None and data["ambient_light"] is not None:
                                # Print the temperature in Celsius and humidity
                                # print(f"Temperature: {data['temp']}°C, Humidity: {data['humidity']}%, Time: {data['time'].strftime('%Y-%m-%d %H:%M:%S')}")
                                
                                # Prepare the data to be published
                                message = {
                                    "temperature": data["temperature"],
                                    "humidity": data["humidity"],
                                    "ambient_light": data["ambient_light"],
                                    "particle_count": data["particle_count"],
                                    "time": data["time"]
                                }

                                # Publish the data to MQTT
                                publish_to_mqtt(message)
                                
                                # Reset data for next reading
                                data["temperature"], data["humidity"], data["ambient_light"], data["particle_count"] = None, None, None, None

                    except ValueError:
                        print(f"Invalid data received on topic '{topic}': {line}")

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
