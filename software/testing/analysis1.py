import csv
import time
import socket
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
acceptable_temp_range = (18, 30)     # Temperature: 18°C to 30°C
acceptable_humid_range = (30, 70)    # Humidity: 30% to 70%
acceptable_light_range = (0, 15)     # Ambient light in lux: 0 to 15
acceptable_particle_range = (0,200)  # Acceptable Range of Particle Count

# Sensor maximum and minimum values
BME280_TEMP_MAX = 85    # Maximum temperature 
BME280_TEMP_MIN = -40   # Minimum temperature 
HUMIDITY_MAX = 100      # Maximum humidity 
HUMIDITY_MIN = 0        # Minimum humidity 

# CSV Files
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context_data.csv"

# Global in-memory cache for measurements.
measurements_cache = []

# Global list to store errors in 5-minute buffer.
fiveminbuff = []

# Initialize CSV Files with headers.
def initialize_csv():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)","Particle Count", "Timestamp"])

    with open(OUT_OF_RANGE_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)","Particle Count", "Timestamp", "Reason"])

    with open(CONTEXT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)","Particle Count", "Timestamp", "Context Type"])

# Function to wait for MQTT broker connection.
def wait_for_mqtt_connection():
    while True:
        try:
            # Attempt to create a socket connection to the MQTT broker.
            sock = socket.create_connection((MQTT_BROKER, MQTT_PORT), timeout=5)
            sock.close()
            print("MQTT broker is available!")
            break  # Exit loop once connection is successful.
        except Exception as e:
            print("MQTT broker not available yet, waiting...")
            time.sleep(2)

# Helper function to extract a datetime object from a measurement.
def extract_timestamp(measurement):
    return datetime.fromisoformat(measurement['time'])

# Update the CSV file with the current 5-hour rolling window.
# The measurements are sorted so that the newest appear first.
def update_csv_file():
    # Sort measurements by timestamp (newest first)
    sorted_measurements = sorted(
        measurements_cache,
        key=extract_timestamp,
        reverse=True
    )
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Particle Count", "Timestamp"])
        for m in sorted_measurements:
            writer.writerow([m['temperature'], m['humidity'], m['ambient_light'], m['particle_count'], m['time']])

# Save an out-of-range measurement into its CSV file.
def save_out_of_range(measurement, reason, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            measurement['temperature'],
            measurement['humidity'],
            measurement['ambient_light'],
            measurement['particle_count'],
            measurement['time'],
            reason,
            context
        ])

# Save context data (surrounding measurements) into its CSV file.
def save_context_data(measurement, context_type):
    with open(CONTEXT_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            measurement['temperature'],
            measurement['humidity'],
            measurement['ambient_light'],
            measurement['particle_count'],
            measurement['time'],
            context_type
        ])

# Publish data over MQTT.
def publish_to_mqtt(topic, message):
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,
        "-m", json.dumps(message)
    ]
    subprocess.run(command)

# Analyze and process an incoming measurement.
def analyze_and_process(measurement):
    global measurements_cache, fiveminbuff

    # Append the new measurement to the in-memory cache.
    measurements_cache.append(measurement)

    # Use current system time to define the rolling 5-hour window.
    cutoff_time = datetime.now() - timedelta(hours=5)
    measurements_cache[:] = [
        m for m in measurements_cache
        if datetime.fromisoformat(m['time']) >= cutoff_time
    ]

    # Update the CSV file with the current rolling window.
    update_csv_file()

    # Convert the measurement time to a datetime object.
    try:
        current_measurement_time = datetime.fromisoformat(measurement['time'])
    except Exception as e:
        print(f"Error parsing measurement time: {measurement['time']} Error: {e}")
        return

    # --- SENSOR RANGE CHECKS ---
    # Temperature range check against BME280 limits.
    if measurement['temperature'] >= BME280_TEMP_MAX:
        print(f"ERROR: Temperature reading {measurement['temperature']}°C exceeds or is equal to the BME280 maximum of {BME280_TEMP_MAX}°C!")
    if measurement['temperature'] <= BME280_TEMP_MIN:
        print(f"ERROR: Temperature reading {measurement['temperature']}°C is below or is equal to the BME280 minimum of {BME280_TEMP_MIN}°C!")

    # Humidity range check if out of sensor limits.
    if measurement['humidity'] >= HUMIDITY_MAX:
        print(f"ERROR: Humidity reading {measurement['humidity']}% exceeds or is equal to the sensor maximum of {HUMIDITY_MAX}%!")
    if measurement['humidity'] <= HUMIDITY_MIN:
        print(f"ERROR: Humidity reading {measurement['humidity']}% is below or is equal to the sensor minimum of {HUMIDITY_MIN}%!")

    # For every new measurement, check if it after the error
    for error in fiveminbuff:
        # Only add measurements that come AFTER the error event.
        if error['error_time'] < current_measurement_time <= error['deadline']:
            save_context_data(measurement, "Surrounding error")

    # Remove any error events whose 5-minute window has expired.
    fiveminbuff[:] = [p for p in fiveminbuff if p['deadline'] >= current_measurement_time]

    # Check for any out-of-range values according to our application acceptable ranges.
    reasons = []
    if not (acceptable_temp_range[0] <= measurement['temperature'] <= acceptable_temp_range[1]):
        reasons.append("Temperature out of range")
    if not (acceptable_humid_range[0] <= measurement['humidity'] <= acceptable_humid_range[1]):
        reasons.append("Humidity out of range")
    if not (acceptable_light_range[0] <= measurement['ambient_light'] <= acceptable_light_range[1]):
        reasons.append("Ambient light out of range")
    if not (acceptable_particle_range[0] <= measurement['particle_count'] <= acceptable_particle_range[1]):
        reasons.append("Particle count out of range")
    
    if reasons:
        context = "Surrounding error readings"
        save_out_of_range(measurement, "; ".join(reasons), context)

        # Immediately capture any context from the cache (readings up to the moment of error detection).
        try:
            out_of_range_time = datetime.fromisoformat(measurement['time'])
        except Exception as e:
            print(f"Error parsing measurement time: {measurement['time']} Error: {e}")
            return

        context_measurements = [
            m for m in measurements_cache
            if abs((datetime.fromisoformat(m['time']) - out_of_range_time).total_seconds()) <= 300
        ]
        for context_measurement in context_measurements:
            context_type = "Exact moment" if context_measurement['time'] == measurement['time'] else "Surrounding Errors"
            save_context_data(context_measurement, context_type)

        # Adds the future readings into 5 min buffer
        fiveminbuff.append({
            'error_time': out_of_range_time,
            'deadline': out_of_range_time + timedelta(seconds=300)
        })

    # Publish the processed measurement over MQTT.
    publish_to_mqtt(OUTPUT_TOPIC, measurement)

# Listen to the MQTT topic and process each received message.
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
                    # Parse the incoming JSON message.
                    message = json.loads(line)

                    # Ensure all required keys are present.
                    if (message.get("temperature") is None or 
                        message.get("humidity") is None or 
                        message.get("ambient_light") is None or 
                        message.get("particle_count") is None or
                        message.get("time") is None):
                        print(f"Incomplete data received on topic '{topic}': {line}")
                        continue

                    analyze_and_process(message)

                except (ValueError, KeyError) as e:
                    print(f"Invalid data received on topic '{topic}': {line}, Error: {e}")

    except Exception as e:
        print(f"Error in listening to topic {topic}: {e}")

# Initialize the CSV files.
initialize_csv()

# Wait for the MQTT broker to be available.
wait_for_mqtt_connection()

# Start the MQTT listener in a separate thread.
combined_thread = Thread(target=listen_to_topic_combined, args=(INPUT_TOPIC,))
combined_thread.start()

# Keep the main thread running.
combined_thread.join()
