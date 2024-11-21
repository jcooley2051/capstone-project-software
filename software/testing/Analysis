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
acceptable_temp_range = (18, 30)  # Example: 18°C to 30°C
acceptable_humid_range = (30, 70)  # Example: 30% to 70%

# CSV Files
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context_data.csv"  # New file for 30-second context data

# Utility Functions for Time Handling
def parse_time(time_str):
    """Parse time string into a datetime object, with error handling."""
    try:
        return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print(f"Invalid time format: {time_str}. Using current time instead.")
        return datetime.now()

def format_time(dt_obj):
    """Format a datetime object into the standard string format."""
    return dt_obj.strftime('%Y-%m-%d %H:%M:%S')

# Initialize CSV Files
def initialize_csv():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Timestamp"])

    with open(OUT_OF_RANGE_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Timestamp", "Context"])

    with open(CONTEXT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Timestamp", "Related To", "Position"])

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

# Save Context Data
def save_context_data(context_measurement, related_to, position):
    with open(CONTEXT_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([context_measurement['temp'], context_measurement['humidity'], context_measurement['time'], related_to, position])

# Publish Data Over MQTT
def publish_to_mqtt(topic, message):
    # Convert any datetime objects in the message to strings
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')  # ISO-like format
        raise TypeError("Type not serializable")

    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,
        "-m", json.dumps(message, default=serialize)  # Use `default` to handle datetime
    ]
    subprocess.run(command)

# Analyze and Process Data
measurements_cache = []

def analyze_and_process(temp, humid, timestamp):
    global measurements_cache

    # Parse and format the timestamp
    timestamp_dt = parse_time(timestamp)
    timestamp = format_time(timestamp_dt)

    measurement = {"temp": temp, "humidity": humid, "time": timestamp}
    save_to_csv(measurement)

    # Add to cache
    measurements_cache.append(measurement)

    # Maintain only recent 60 seconds in the cache
    measurements_cache = [
        m for m in measurements_cache
        if parse_time(m['time']) >= timestamp_dt - timedelta(seconds=60)
    ]

    # Analysis for out-of-range values
    if not (acceptable_temp_range[0] <= temp <= acceptable_temp_range[1]) or not (acceptable_humid_range[0] <= humid <= acceptable_humid_range[1]):
        context = f"Out-of-range measurement at {timestamp}"
        save_out_of_range(measurement, context)

        # Pull 30 seconds before and after the out-of-range timestamp
        context_measurements = [
            m for m in measurements_cache
            if timestamp
