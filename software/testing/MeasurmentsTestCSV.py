import csv
from datetime import datetime
import subprocess
import json
from threading import Thread

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1337
OUTPUT_TOPIC = "analysis/results"
INPUT_TOPIC = "reading/formatted"

# Acceptable Ranges
acceptable_temp_range = (18, 30)  # Example: 18°C to 30°C
acceptable_humid_range = (30, 70)  # Example: 30% to 70%

# CSV Files
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"

# Initialize CSV Files
def initialize_csv():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Timestamp"])

    with open(OUT_OF_RANGE_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Timestamp", "Context"])

# Save Measurement to CSV
def save_to_csv(measurement):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temp'], measurement['humidity'], measurement['time']])

# Save Out-of-Range Measurement
def save_out_of_range(measurement, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temp'], measurement['humidity'], measurement['time'], context])

# Publish Data Over MQTT
def publish_to_mqtt(topic, message):
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,
        "-m", json.dumps(message)
    ]
    subprocess.run(command)

# Analyze and Process Data
def analyze_and_process(temp, humid, timestamp):
    measurement = {"temp": temp, "humidity": humid, "time": timestamp}
    save_to_csv(measurement)

    # Analysis for out-of-range values
    if not (acceptable_temp_range[0] <= temp <= acceptable_temp_range[1]) or not (acceptable_humid_range[0] <= humid <= acceptable_humid_range[1]):
        context = f"Out-of-range measurement at {timestamp}"
        save_out_of_range(measurement, context)
        print(f"Out-of-range detected: {measurement}")

    # Publish processed results
    publish_to_mqtt(OUTPUT_TOPIC, measurement)

# MQTT Listener for Combined Data
def listen_to_topic_combined(topic):
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
                    # Parse the JSON message
                    message = json.loads(line)

                    # Extract values
                    temp = message["temp"]
                    humidity = message["humidity"]
                    timestamp = message["time"]

                    # Process the combined data
                    analyze_and_process(temp, humidity, timestamp)

                except (ValueError, KeyError) as e:
                    print(f"Invalid data received on topic '{topic}': {line}, Error: {e}")

    except Exception as e:
        print(f"Error in listening to topic {topic}: {e}")

# Initialize CSVs
initialize_csv()

# Create and Start Thread for Listening to Combined Topic
combined_thread = Thread(target=listen_to_topic_combined, args=(INPUT_TOPIC,))

combined_thread.start()

# Wait for the Thread to Finish
combined_thread.join()
