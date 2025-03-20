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
acceptable_temp_range = (18, 30)     # Temperature in °C
acceptable_humid_range = (30, 70)      # Humidity in %
acceptable_light_range = (0, 15)       # Ambient light in lux
acceptable_particle_range = (0, 1000)  # Particle count

# Acceptable Vibration Range (each axis: x, y, z)
acceptable_vibration_range = {
    'x': (-0.5, 0.5),
    'y': (-0.5, 0.5),
    'z': (-0.5, 0.5)
}

# Sensor extremes
BME280_TEMP_MAX = 85    
BME280_TEMP_MIN = -40   
HUMIDITY_MAX = 100      
HUMIDITY_MIN = 0        
VEML7700_MAX_LIGHT = 120000
IH_PMC_001_MAX = 1000   

# CSV Files (includes Node column)
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context_data.csv"

# In-memory cache for 5-hour measurements.
measurements_cache = []

# List to store error events in a 5-minute window.
fiveminbuff = []

def initialize_csv():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Node", "Temperature (°C)", "Humidity (%)", "Ambient Light (lux)",
                         "Particle Count", "Vibration", "Timestamp", "Context"])
    with open(OUT_OF_RANGE_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Node", "Temperature (°C)", "Humidity (%)", "Ambient Light (lux)",
                         "Particle Count", "Vibration", "Timestamp", "Reason", "Context"])
    with open(CONTEXT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Node", "Temperature (°C)", "Humidity (%)", "Ambient Light (lux)",
                         "Particle Count", "Vibration", "Timestamp", "Context Type"])

def update_csv_file():
    sorted_measurements = sorted(measurements_cache, key=lambda m: datetime.fromisoformat(m['time']), reverse=True)
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Node", "Temperature (°C)", "Humidity (%)", "Ambient Light (lux)",
                         "Particle Count", "Vibration", "Timestamp"])
        for m in sorted_measurements:
            writer.writerow([
                m.get("node"),
                m.get("temperature"),
                m.get("humidity"),
                m.get("ambient_light"),
                m.get("particle_count"),
                json.dumps(m.get("vibration")),
                m.get("time")
            ])

def save_out_of_range(measurement, reason, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            measurement.get("node"),
            measurement.get("temperature"),
            measurement.get("humidity"),
            measurement.get("ambient_light"),
            measurement.get("particle_count"),
            json.dumps(measurement.get("vibration")),
            measurement.get("time"),
            reason,
            context
        ])

def save_context_data(measurement, context_type):
    with open(CONTEXT_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            measurement.get("node"),
            measurement.get("temperature"),
            measurement.get("humidity"),
            measurement.get("ambient_light"),
            measurement.get("particle_count"),
            json.dumps(measurement.get("vibration")),
            measurement.get("time"),
            context_type
        ])

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

def publish_to_mqtt(topic, message):
    command = [
        "mosquitto_pub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic,
        "-m", json.dumps(message)
    ]
    subprocess.run(command)

# Process and publish a single node's measurement.
def analyze_and_process_node(measurement):
    # Add current time if not present.
    if not measurement.get("time"):
        measurement["time"] = datetime.now().isoformat()
    measurements_cache.append(measurement)
    cutoff_time = datetime.now() - timedelta(hours=5)
    measurements_cache[:] = [m for m in measurements_cache if datetime.fromisoformat(m['time']) >= cutoff_time]
    update_csv_file()
    
    node_id = measurement.get("node", "Unknown")
    reasons = []
    
    # Temperature check
    temp = measurement.get("temperature")
    if temp is not None:
        if temp >= BME280_TEMP_MAX:
            print(f"WARNING: {node_id} Temperature {temp}°C is at or above max limit ({BME280_TEMP_MAX}°C)!")
        if temp <= BME280_TEMP_MIN:
            print(f"WARNING: {node_id} Temperature {temp}°C is at or below min limit ({BME280_TEMP_MIN}°C)!")
        if not (acceptable_temp_range[0] <= temp <= acceptable_temp_range[1]):
            reasons.append("Temperature out of range")
    
    # Humidity check
    humid = measurement.get("humidity")
    if humid is not None:
        if humid >= HUMIDITY_MAX:
            print(f"WARNING: {node_id} Humidity {humid}% is at or above max limit ({HUMIDITY_MAX}%)!")
        if humid <= HUMIDITY_MIN:
            print(f"WARNING: {node_id} Humidity {humid}% is at or below min limit ({HUMIDITY_MIN}%)!")
        if not (acceptable_humid_range[0] <= humid <= acceptable_humid_range[1]):
            reasons.append("Humidity out of range")
    
    # Ambient light check
    light = measurement.get("ambient_light")
    if light is not None:
        if light >= VEML7700_MAX_LIGHT:
            print(f"WARNING: {node_id} Ambient Light {light} is at or above the max limit ({VEML7700_MAX_LIGHT})")
        if not (acceptable_light_range[0] <= light <= acceptable_light_range[1]):
            reasons.append("Ambient light out of range")
    
    # Particle count check
    particle = measurement.get("particle_count")
    if particle is not None:
        if particle >= IH_PMC_001_MAX:
            print(f"WARNING: {node_id} Particle Count {particle} is at or above max limit ({IH_PMC_001_MAX})")
        if not (acceptable_particle_range[0] <= particle <= acceptable_particle_range[1]):
            reasons.append("Particle count out of range")
    
    # Vibration check (only if valid list data provided)
    vib = measurement.get("vibration")
    if isinstance(vib, list) and len(vib) >= 3:
        x, y, z = vib[0], vib[1], vib[2]
        if not (acceptable_vibration_range['x'][0] <= x <= acceptable_vibration_range['x'][1] and
                acceptable_vibration_range['y'][0] <= y <= acceptable_vibration_range['y'][1] and
                acceptable_vibration_range['z'][0] <= z <= acceptable_vibration_range['z'][1]):
            reasons.append("Vibration out of range")
    # If vibration is missing or not valid, we do not add an error here.
    
    if reasons:
        msg = f"WARNING: {node_id} measurement out of bounds! Issues: {', '.join(reasons)}"
        print(msg)
        save_out_of_range(measurement, "; ".join(reasons), "Surrounding error readings")
        # Save context data for measurements within 5 minutes.
        current_time = datetime.fromisoformat(measurement["time"])
        for m in measurements_cache:
            try:
                t = datetime.fromisoformat(m["time"])
                if abs((t - current_time).total_seconds()) <= 300:
                    context_type = "Exact moment" if m["time"] == measurement["time"] else "Surrounding Errors"
                    save_context_data(m, context_type)
            except Exception:
                continue
        fiveminbuff.append({
            'error_time': current_time,
            'deadline': current_time + timedelta(seconds=300)
        })
    
    # Process post-error context events.
    current_time = datetime.fromisoformat(measurement["time"])
    for event in fiveminbuff.copy():
        if event['error_time'] < current_time <= event['deadline']:
            save_context_data(measurement, "Surrounding Errors (post)")
        if current_time > event['deadline']:
            fiveminbuff.remove(event)
    
    publish_to_mqtt(OUTPUT_TOPIC, measurement)

# If message contains separate node dictionaries, process each individually.
def process_node_data(node_data, node_name, overall_time):
    measurement = {
        "node": node_name,
        "temperature": node_data.get("temperature"),
        "humidity": node_data.get("humidity"),
        "ambient_light": node_data.get("ambient_light"),
        "particle_count": node_data.get("particle_count"),
        "vibration": node_data.get("vibration"),
        "time": overall_time
    }
    analyze_and_process_node(measurement)

def listen_to_topic_combined(topic):
    command = ["mosquitto_sub", "-h", MQTT_BROKER, "-p", str(MQTT_PORT), "-t", topic]
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                print(f"DEBUG: Received message: {line}")
                try:
                    message = json.loads(line)
                    # If message is already flat (with "node"), process directly.
                    if "node" in message:
                        analyze_and_process_node(message)
                    # Otherwise, if message contains separate node dictionaries, process each.
                    elif all(k in message for k in ["PL_data", "SC_data", "SP_data"]):
                        overall_time = message.get("time", datetime.now().isoformat())
                        process_node_data(message["PL_data"], "PL", overall_time)
                        process_node_data(message["SC_data"], "SC", overall_time)
                        process_node_data(message["SP_data"], "SP", overall_time)
                    else:
                        print(f"Incomplete data received on topic '{topic}': {line}")
                except Exception as e:
                    print(f"Error processing message: {line}, Error: {e}")
    except Exception as e:
        print(f"Error in listening to topic {topic}: {e}")

initialize_csv()
wait_for_mqtt_connection()

combined_thread = Thread(target=listen_to_topic_combined, args=(INPUT_TOPIC,))
combined_thread.start()
combined_thread.join()
