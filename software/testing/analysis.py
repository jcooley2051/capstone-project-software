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
acceptable_humid_range = (30, 70)      # Humidity: 30% to 70%
acceptable_light_range = (0, 100)       # Ambient light in lux: 0 to 15
acceptable_particle_range = (0, 1000)  # Acceptable Range of Particle Count

# Acceptable Vibration Range (for each axis: x, y, z)
acceptable_vibration_range = {
    'x': (-0.5, 0.5),
    'y': (-0.5, 0.5),
    'z': (-0.5, 0.5)
}

# Sensor maximum and minimum values
BME280_TEMP_MAX = 85    # Maximum temperature 
BME280_TEMP_MIN = -40   # Minimum temperature 
HUMIDITY_MAX = 100      # Maximum humidity 
HUMIDITY_MIN = 0        # Minimum humidity 
VEML7700_MAX_LIGHT = 120000 # Maximum light readings
IH_PMC_001_MAX = 1000   # Max particle count 

# CSV Files
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context_data.csv"

# Global in-memory cache for 5 hour measurements.
measurements_cache = []

# Global list to store errors in 5-minute buffer.
fiveminbuff = []

# Initialize CSV Files with headers.
def initialize_csv():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Particle Count", "Vibration", "Timestamp", "Context"])

    with open(OUT_OF_RANGE_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Particle Count", "Vibration", "Timestamp", "Reason", "Context"])

    with open(CONTEXT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Particle Count", "Vibration", "Timestamp", "Context Type"])

# Function to publish result over MQTT
def publish_result(result):
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", OUTPUT_TOPIC,
        "-m", json.dumps(result)
    ]
    try:
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"Error publishing MQTT message: {e}")

# Function to wait for MQTT broker connection
def wait_for_mqtt_connection():
    while True:
        try:
            sock = socket.create_connection((MQTT_BROKER, MQTT_PORT), timeout=5)
            sock.close()
            print("MQTT broker is available!")
            break
        except Exception:
            print("MQTT broker not available yet, waiting...")
            time.sleep(2)

# Function to publish the MQTT readings 
def publish_to_mqtt(topic, message):
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,
        "-m", json.dumps(message)
    ]
    subprocess.run(command)

# Update the CSV file with the current 5-hour rolling buffer
def update_csv_file():
    sorted_measurements = sorted(measurements_cache, key=lambda m: datetime.fromisoformat(m['time']), reverse=True)
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Temperature (°C)", "Humidity (%)", "Ambient Light (lux)", "Particle Count", "Vibration", "Timestamp"])
        for m in sorted_measurements:
            writer.writerow([m['temperature'], m['humidity'], m['ambient_light'], m['particle_count'], json.dumps(m['vibration']), m['time']])

# Save an out-of-range measurement into its CSV file
def save_out_of_range(measurement, reason, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temperature'], measurement['humidity'], measurement['ambient_light'], measurement['particle_count'], json.dumps(measurement['vibration']), measurement['time'], reason, context])

# Save context data (surrounding measurements) into its CSV file.
def save_context_data(measurement, context_type):
    with open(CONTEXT_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([measurement['temperature'], measurement['humidity'], measurement['ambient_light'], measurement['particle_count'], json.dumps(measurement['vibration']), measurement['time'], context_type])

# Early warning detection: Check if recent measurements show a trend toward a sensor's upper bound.
def check_early_warning(measurement):
    # Standard sensors early warning.
    if len(measurements_cache) < 3:
        return
    sorted_measurements = sorted(measurements_cache, key=lambda m: datetime.fromisoformat(m['time']))
    recent = sorted_measurements[-3:]
    
    acceptable_max = {
        'temperature': acceptable_temp_range[1],
        'humidity': acceptable_humid_range[1],
        'ambient_light': acceptable_light_range[1],
        'particle_count': acceptable_particle_range[1]
    }
    warning_margins = {
        'temperature': 2,      # degrees Celsius
        'humidity': 5,         # percentage points
        'ambient_light': 2,    # lux
        'particle_count': 50  # particle count units
    }
    
    sensors = ['temperature', 'humidity', 'ambient_light', 'particle_count']
    for sensor in sensors:
        if recent[0][sensor] < recent[1][sensor] < recent[2][sensor]:
            if measurement[sensor] >= acceptable_max[sensor] - warning_margins[sensor]:
                print(f"Early Warning: {sensor} reading is gradually increasing and nearing its bound. Current value: {measurement[sensor]}")
    
    # Early Warning Detection for Vibration
    if len(measurements_cache) >= 3:
        sorted_vib = sorted(measurements_cache, key=lambda m: datetime.fromisoformat(m['time']))
        recent_vib = sorted_vib[-3:]
        for axis, idx in zip(['x', 'y', 'z'], [0, 1, 2]):
            try:
                if (recent_vib[0]['vibration'][idx] < recent_vib[1]['vibration'][idx] < recent_vib[2]['vibration'][idx]):
                    current_value = measurement['vibration'][idx]
                    warning_margin = 0.1  # Adjustable margin for vibration
                    if current_value >= acceptable_vibration_range[axis][1] - warning_margin:
                        print(f"Early Warning: Vibration {axis}-axis reading is gradually increasing and nearing its upper bound. Current value: {current_value}")
            except Exception as e:
                print(f"Error checking early warning for vibration axis {axis}: {e}")

# Analyze and process an incoming measurement
def analyze_and_process(measurement):
    global measurements_cache, fiveminbuff

    measurements_cache.append(measurement)
    
    # Maintain a rolling 5-hour buffer.
    cutoff_time = datetime.now() - timedelta(hours=5)
    measurements_cache[:] = [m for m in measurements_cache if datetime.fromisoformat(m['time']) >= cutoff_time]

    update_csv_file()

    try:
        current_measurement_time = datetime.fromisoformat(measurement['time'])
    except Exception as e:
        print(f"Error parsing measurement time: {measurement['time']} Error: {e}")
        return

    # SENSOR RANGE CHECKS TO MAKE SURE WORKING CORRECTLY
    if measurement['temperature'] >= BME280_TEMP_MAX:
        print(f"WARNING: Temperature {measurement['temperature']}°C is at or above max limit ({BME280_TEMP_MAX}°C)!")
    if measurement['temperature'] <= BME280_TEMP_MIN:
        print(f"WARNING: Temperature {measurement['temperature']}°C is at or below min limit ({BME280_TEMP_MIN}°C)!")
    if measurement['humidity'] >= HUMIDITY_MAX:
        print(f"WARNING: Humidity {measurement['humidity']}% is at or above max limit ({HUMIDITY_MAX}%)!")
    if measurement['humidity'] <= HUMIDITY_MIN:
        print(f"WARNING: Humidity {measurement['humidity']}% is at or below min limit ({HUMIDITY_MIN}%)!")
    if measurement['ambient_light'] >= VEML7700_MAX_LIGHT:
        print(f"WARNING: Light {measurement['ambient_light']} is at or above the max limit ({VEML7700_MAX_LIGHT})")
    if measurement['particle_count'] >= IH_PMC_001_MAX:
        print(f"WARNING: Particle Count {measurement['particle_count']} is at or above max limit ({IH_PMC_001_MAX})")
    # Check for any out-of-range values according to the acceptable ranges.
    reasons = []
    if not (acceptable_temp_range[0] <= measurement['temperature'] <= acceptable_temp_range[1]):
        reasons.append("Temperature out of range")
    if not (acceptable_humid_range[0] <= measurement['humidity'] <= acceptable_humid_range[1]):
        reasons.append("Humidity out of range")
    if not (acceptable_light_range[0] <= measurement['ambient_light'] <= acceptable_light_range[1]):
        reasons.append("Ambient light out of range")
    if not (acceptable_particle_range[0] <= measurement['particle_count'] <= acceptable_particle_range[1]):
        reasons.append("Particle count out of range")
    
    # Check vibration reading.
    try:
        x, y, z = measurement['vibration']
        if not (acceptable_vibration_range['x'][0] <= x <= acceptable_vibration_range['x'][1] and
                acceptable_vibration_range['y'][0] <= y <= acceptable_vibration_range['y'][1] and
                acceptable_vibration_range['z'][0] <= z <= acceptable_vibration_range['z'][1]):
            reasons.append("Vibration out of range")
    except Exception as e:
        reasons.append("Invalid vibration data")
    
    if reasons:
        msg = f"WARNING: Measurement approaching out of bounds! Issues detected: {', '.join(reasons)}"
        print(msg)
        
        save_out_of_range(measurement, "; ".join(reasons), "Surrounding error readings")

        # Use the current measurement time as the error time
        out_of_range_time = current_measurement_time

        # Immediately save context data for measurements in the past 5 minutes (if any)
        context_measurements = [
            m for m in measurements_cache
            if abs((datetime.fromisoformat(m['time']) - out_of_range_time).total_seconds()) <= 300
        ]
        for context_measurement in context_measurements:
            context_type = "Exact moment" if context_measurement['time'] == measurement['time'] else "Surrounding Errors"
            save_context_data(context_measurement, context_type)

        # Add the error event to the 5-minute buffer to capture future (post-error) measurements.
        fiveminbuff.append({
            'error_time': out_of_range_time,
            'deadline': out_of_range_time + timedelta(seconds=300)
        })

    # Get any errors into 5 min buffer.
    for event in fiveminbuff.copy():
        if event['error_time'] < current_measurement_time <= event['deadline']:
            save_context_data(measurement, "Surrounding Errors (post)")
        # Remove error events that have passed their time.
        if current_measurement_time > event['deadline']:
            fiveminbuff.remove(event)
    
    # EARLY WARNING TREND CHECK 
    check_early_warning(measurement)
    # Finally, publish the processed measurement over MQTT.
    publish_to_mqtt(OUTPUT_TOPIC, measurement)

# Listen to the MQTT topic and process each received message.
def listen_to_topic_combined(topic):
    command = ["mosquitto_sub", "-h", MQTT_BROKER, "-p", str(MQTT_PORT), "-t", topic]
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                line = line.strip()
                try:
                    message = json.loads(line)
                    # Check if message has the required readings.
                    if all(k in message for k in ["temperature", "humidity", "ambient_light", "particle_count", "time", "vibration"]):
                        analyze_and_process(message)
                    else:
                        print(f"Incomplete data received on topic '{topic}': {line}")
                except (ValueError, KeyError) as e:
                    print(f"Invalid data received on topic '{topic}': {line}, Error: {e}")
    except Exception as e:
        print(f"Error in listening to topic {topic}: {e}")

# Initialize CSV files.
initialize_csv()

# Wait for the MQTT broker to be available.
wait_for_mqtt_connection()

# Start the MQTT listener in a separate thread.
combined_thread = Thread(target=listen_to_topic_combined, args=(INPUT_TOPIC,))
combined_thread.start()

# Keep the main thread running.
combined_thread.join()
