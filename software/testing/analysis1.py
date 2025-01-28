import csv
from datetime import datetime, timedelta
import subprocess
import json
from threading import Thread

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1337
OUTPUT_TOPIC = "analysis/results"
INPUT_TOPIC = "reading/formatted"

# Acceptable Ranges
acceptable_temp_range = (18, 30)  # Range: 0°C to 50°C
acceptable_humid_range = (30, 70)  # Range: 30% to 70%
acceptable_light_range = (800, 1000)  # Range: Ambient light in lux

# CSV Files
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context.csv"

# Initialize CSV Files
def initialize_csv():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Timestamp"])

    with open(OUT_OF_RANGE_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Timestamp", "Reason", "Context"])

    with open(CONTEXT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Timestamp", "Context Type"])

# Save Measurement to CSV
def save_to_csv(measurement):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temperature'], measurement['humidity'], measurement['ambient_light'], measurement['time']])

# Save Out-of-Range Measurement
def save_out_of_range(measurement, reason, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temperature'], measurement['humidity'], measurement['ambient_light'], measurement['time'], reason, context])

# Save Context Data
def save_context_data(measurement, context_type):
    with open(CONTEXT_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temperature'], measurement['humidity'], measurement['ambient_light'], measurement['time'], context_type])

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
measurements_cache = []

def analyze_and_process(measurement):
    global measurements_cache

    save_to_csv(measurement)

    # Add to cache
    measurements_cache.append(measurement)

    # Maintain only recent 5 hours in the cache
    cutoff_time = datetime.fromisoformat(measurement['time']) - timedelta(hours=5)
    measurements_cache = [
        m for m in measurements_cache
        if datetime.fromisoformat(m['time']) >= cutoff_time
    ]

    # Check for out-of-range values
    reasons = []
    if not (acceptable_temp_range[0] <= measurement['temperature'] <= acceptable_temp_range[1]):
        reasons.append("Temperature out of range")
    if not (acceptable_humid_range[0] <= measurement['humidity'] <= acceptable_humid_range[1]):
        reasons.append("Humidity out of range")
    if not (acceptable_light_range[0] <= measurement['ambient_light'] <= acceptable_light_range[1]):
        reasons.append("Ambient light out of range")

    if reasons:
        context = "Surrounding error readings"
        save_out_of_range(measurement, "; ".join(reasons), context)

        # Find and save surrounding error context
        out_of_range_time = datetime.fromisoformat(measurement['time'])
        context_measurements = [
            m for m in measurements_cache
            if abs((datetime.fromisoformat(m['time']) - out_of_range_time).total_seconds()) <= 300
        ]

        for context_measurement in context_measurements:
            context_type = "Exact moment" if context_measurement['time'] == measurement['time'] else "Surrounding"
            save_context_data(context_measurement, context_type)

    # Publish processed results
    publish_to_mqtt(OUTPUT_TOPIC, measurement)

# MQTT Listener
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
                    temp = message.get("temperature")
                    humid = message.get("humidity")
                    light = message.get("ambient_light")
                    timestamp = message.get("time")

                    if temp is None or humid is None or light is None or timestamp is None:
                        print(f"Incomplete data received on topic '{topic}': {line}")
                        continue

                    # Process the combined data
                    analyze_and_process(message)

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
