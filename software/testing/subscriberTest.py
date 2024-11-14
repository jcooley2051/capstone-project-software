import subprocess
import json

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "/reading/formatted"

# Function to listen to the MQTT topic using subprocess
def listen_to_formatted_topic():
    """Listen to the /reading/formatted topic and process the received messages."""
    print(f"Listening to topic: {MQTT_TOPIC}")  # Debugging statement to confirm the script is running
    
    # Command to subscribe to the MQTT topic
    command = [
        "mosquitto_sub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", MQTT_TOPIC
    ]

    try:
        # Start the subprocess to listen to the MQTT topic
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                line = line.strip()
                print(f"Received line on {MQTT_TOPIC}: {line}")  # Debugging statement to check the received data
                
                try:
                    # Parse the received line as JSON
                    message = json.loads(line)
                    print(f"Processed message: {message}")  # Print the parsed message
                except json.JSONDecodeError:
                    print(f"Failed to decode message: {line}")
                
    except Exception as e:
        print(f"Error in listening to topic {MQTT_TOPIC}: {e}")

# Call the function to start listening
listen_to_formatted_topic()


