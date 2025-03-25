import csv
import time
import socket
from datetime import datetime, timedelta
import subprocess
import json
from threading import Thread

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
OUTPUT_TOPIC = "analysis/results"
INPUT_TOPIC = "reading/formatted"

# Acceptable Ranges 
acceptable_temp_range = (18, 30)     # Temperature in °C
acceptable_humid_range = (30, 70)      # Humidity in %
acceptable_light_range = (0, 30)       # Ambient light in lux
acceptable_particle_range = (0, 1000)  # Particle count

# New vibration limits
VIBRATION_MIN = 0.0
VIBRATION_MAX = 0.5

# Sensor extreme values
BME280_TEMP_MAX = 85    
BME280_TEMP_MIN = -40   
HUMIDITY_MAX = 100      
HUMIDITY_MIN = 0        
VEML7700_MAX_LIGHT = 120000
IH_PMC_001_MAX = 1000   

# CSV Files
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context_data.csv"

# Global in-memory cache for 5-hour measurements.
measurements_cache = []

# Global list to store error events in a 5-minute buffer.
fiveminbuff = []

# If there is none, convert to empty string.
def safe_str(val):
    return str(val) if val is not None else ""

# Creation of all CSV files.
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

# Updates CSV with newest readings.
def update_csv_file():
    sorted_measurements = sorted(measurements_cache, key=lambda m: datetime.fromisoformat(m['time']), reverse=True)
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Node", "Temperature (°C)", "Humidity (%)", "Ambient Light (lux)",
                         "Particle Count", "Vibration", "Timestamp"])
        for m in sorted_measurements:
            writer.writerow([
                safe_str(m.get("node")),
                safe_str(m.get("temperature")),
                safe_str(m.get("humidity")),
                safe_str(m.get("ambient_light")),
                safe_str(m.get("particle_count")),
                safe_str(m.get("vibration")),
                safe_str(m.get("time"))
            ])

# Saves all out of range readings.
def save_out_of_range(measurement, reason, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            safe_str(measurement.get("node")),
            safe_str(measurement.get("temperature")),
            safe_str(measurement.get("humidity")),
            safe_str(measurement.get("ambient_light")),
            safe_str(measurement.get("particle_count")),
            safe_str(measurement.get("vibration")),
            safe_str(measurement.get("time")),
            safe_str(reason),
            safe_str(context)
        ])

# Save 5 minutes before and after an out-of-range reading.
def save_context_data(measurement, context_type):
    with open(CONTEXT_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            safe_str(measurement.get("node")),
            safe_str(measurement.get("temperature")),
            safe_str(measurement.get("humidity")),
            safe_str(measurement.get("ambient_light")),
            safe_str(measurement.get("particle_count")),
            safe_str(measurement.get("vibration")),
            safe_str(measurement.get("time")),
            safe_str(context_type)
        ])

# Check to make sure MQTT is set up.
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

def check_null(data):
    if (data["PL_data"].get("temperature") is None and
        data["SC_data"].get("temperature") is None and
        data["SP_data"].get("temperature") is None):
        return True
    return False

# Modified early warning function that returns True if an early warning condition is met.
def check_early_warning(measurement):
    node_id = measurement.get("node", "Unknown")
    node_measurements = [m for m in measurements_cache if m.get("node", "Unknown") == node_id]
    if len(node_measurements) < 3:
        return False
    sorted_measurements = sorted(node_measurements, key=lambda m: datetime.fromisoformat(m['time']))
    recent = sorted_measurements[-3:]
    
    acceptable_max = {
        'temperature': acceptable_temp_range[1],
        'humidity': acceptable_humid_range[1],
        'ambient_light': acceptable_light_range[1],
        'particle_count': acceptable_particle_range[1],
        'vibration': VIBRATION_MAX
    }
    warning_margins = {
        'temperature': 2,      # degrees Celsius
        'humidity': 5,         # percentage points
        'ambient_light': 2,    # lux
        'particle_count': 100, # particle count units
        'vibration': 0.05      # vibration units
    }
    
    sensors = ['temperature', 'humidity', 'ambient_light', 'particle_count', 'vibration']
    triggered = False
    for sensor in sensors:
        if sensor not in recent[0] or sensor not in recent[1] or sensor not in recent[2]:
            continue
        if recent[0][sensor] < recent[1][sensor] < recent[2][sensor]:
            if sensor in measurement and isinstance(measurement[sensor], (int, float)):
                if measurement[sensor] >= acceptable_max[sensor] - warning_margins[sensor]:
                    print(f"Early Warning: {sensor} reading for node {node_id} is gradually increasing and nearing its bound. Current value: {measurement[sensor]}")
                    triggered = True
    return triggered

# analyze_and_process_node updates caches, CSVs, and warnings.
def analyze_and_process_node(measurement, publish=True):
    global measurements_cache, fiveminbuff

    if not measurement.get("time"):
        measurement["time"] = datetime.now().isoformat()
    measurements_cache.append(measurement)
    cutoff_time = datetime.now() - timedelta(hours=5)
    measurements_cache[:] = [m for m in measurements_cache if datetime.fromisoformat(m['time']) >= cutoff_time]
    update_csv_file()

    try:
        current_time = datetime.fromisoformat(measurement["time"])
    except Exception as e:
        print(f"Error parsing measurement time: {measurement.get('time')} Error: {e}")
        return

    node_id = measurement.get("node", "Unknown")
    reasons = []
    
    temp = measurement.get("temperature")
    if temp is not None:
        if temp >= BME280_TEMP_MAX:
            print(f"WARNING: {node_id} Temperature {temp}°C is at or above max limit ({BME280_TEMP_MAX}°C)!")
        if temp <= BME280_TEMP_MIN:
            print(f"WARNING: {node_id} Temperature {temp}°C is at or below min limit ({BME280_TEMP_MIN}°C)!")
        if not (acceptable_temp_range[0] <= temp <= acceptable_temp_range[1]):
            reasons.append("Temperature out of range")
    
    humid = measurement.get("humidity")
    if humid is not None:
        if humid >= HUMIDITY_MAX:
            print(f"WARNING: {node_id} Humidity {humid}% is at or above max limit ({HUMIDITY_MAX}%)!")
        if humid <= HUMIDITY_MIN:
            print(f"WARNING: {node_id} Humidity {humid}% is at or below min limit ({HUMIDITY_MIN}%)!")
        if not (acceptable_humid_range[0] <= humid <= acceptable_humid_range[1]):
            reasons.append("Humidity out of range")
    
    light = measurement.get("ambient_light")
    if light is not None:
        if light >= VEML7700_MAX_LIGHT:
            print(f"WARNING: {node_id} Ambient Light {light} is at or above the max limit ({VEML7700_MAX_LIGHT})")
        if not (acceptable_light_range[0] <= light <= acceptable_light_range[1]):
            reasons.append("Ambient light out of range")
    
    particle = measurement.get("particle_count")
    if particle is not None:
        if particle >= IH_PMC_001_MAX:
            print(f"WARNING: {node_id} Particle Count {particle} is at or above max limit ({IH_PMC_001_MAX})")
        if not (acceptable_particle_range[0] <= particle <= acceptable_particle_range[1]):
            reasons.append("Particle count out of range")
    
    vib = measurement.get("vibration")
    if vib is not None:
        try:
            if not (VIBRATION_MIN <= float(vib) <= VIBRATION_MAX):
                reasons.append("Vibration out of range")
        except Exception as e:
            reasons.append("Invalid vibration data")
    
    if reasons:
        msg = f"WARNING: {node_id} measurement out of bounds! Issues detected: {', '.join(reasons)}"
        print(msg)
        save_out_of_range(measurement, "; ".join(reasons), "Surrounding error readings")
        for m in measurements_cache:
            try:
                if m.get("node") == node_id:
                    t = datetime.fromisoformat(m["time"])
                    if abs((t - current_time).total_seconds()) <= 300:
                        context_type = "Exact moment" if m["time"] == measurement["time"] else "Surrounding Errors"
                        save_context_data(m, context_type)
            except Exception:
                continue
        fiveminbuff.append({
            'error_time': current_time,
            'deadline': current_time + timedelta(seconds=300),
            'node': node_id
        })
    
    # Determine overall status based on sensor checks and early warning.
    early_warning_flag = check_early_warning(measurement)
    if reasons:
        measurement["status"] = "bad"
    elif early_warning_flag:
        measurement["status"] = "degraded"
    else:
        measurement["status"] = "good"
    
    for event in fiveminbuff.copy():
        if event['node'] == node_id and event['error_time'] < current_time <= event['deadline']:
            save_context_data(measurement, "Surrounding Errors (post)")
        if current_time > event['deadline']:
            fiveminbuff.remove(event)
    
    # Create a copy of the measurement for publishing units without altering the cached raw data.
    publish_measurement = measurement.copy()
    sensor_units = {
        "temperature": " °C",
        "humidity": " %",
        "ambient_light": " lux",
        "particle_count": " particles",
        "vibration": " g"
    }
    for sensor, unit in sensor_units.items():
        if sensor in publish_measurement and publish_measurement[sensor] is not None:
            try:
                numeric_value = float(publish_measurement[sensor])
                publish_measurement[sensor] = f"{numeric_value}{unit}"
            except Exception:
                if not str(publish_measurement[sensor]).endswith(unit):
                    publish_measurement[sensor] = f"{publish_measurement[sensor]}{unit}"
    
    if publish:
        publish_to_mqtt(OUTPUT_TOPIC, publish_measurement)

# process_node_data now builds the measurement dictionary only with available sensor keys.
def process_node_data(node_data, node_name, overall_time, publish=True):
    measurement = {"node": node_name, "time": overall_time}
    if node_data.get("temperature") is not None:
        measurement["temperature"] = node_data.get("temperature")
    if node_data.get("humidity") is not None:
        measurement["humidity"] = node_data.get("humidity")
    if node_data.get("ambient_light") is not None:
        measurement["ambient_light"] = node_data.get("ambient_light")
    if node_data.get("particle_count") is not None:
        measurement["particle_count"] = node_data.get("particle_count")
    if node_data.get("vibration") is not None:
        measurement["vibration"] = node_data.get("vibration")
    
    analyze_and_process_node(measurement, publish=publish)
    
    # Create a copy with units appended to return for combined messages.
    published_measurement = measurement.copy()
    sensor_units = {
        "temperature": " °C",
        "humidity": " %",
        "ambient_light": " lux",
        "particle_count": " particles",
        "vibration": " g"
    }
    for sensor, unit in sensor_units.items():
        if sensor in published_measurement and published_measurement[sensor] is not None:
            try:
                numeric_value = float(published_measurement[sensor])
                published_measurement[sensor] = f"{numeric_value}{unit}"
            except Exception:
                if not str(published_measurement[sensor]).endswith(unit):
                    published_measurement[sensor] = f"{published_measurement[sensor]}{unit}"
    return published_measurement

# When a combined message is received, process each station without publishing individually.
def listen_to_topic_combined(topic):
    command = ["mosquitto_sub", "-h", MQTT_BROKER, "-p", str(MQTT_PORT), "-t", topic]
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                    if "node" in message:
                        analyze_and_process_node(message)
                    elif all(k in message for k in ["PL_data", "SC_data", "SP_data"]):
                        overall_time = message.get("time", datetime.now().isoformat())
                        pl_measurement = process_node_data(message["PL_data"], "PL", overall_time, publish=False)
                        sc_measurement = process_node_data(message["SC_data"], "SC", overall_time, publish=False)
                        sp_measurement = process_node_data(message["SP_data"], "SP", overall_time, publish=False)
                        combined_message = {
                            "PL_data": pl_measurement,
                            "SC_data": sc_measurement,
                            "SP_data": sp_measurement,
                            "time": overall_time
                        }
                        publish_to_mqtt(OUTPUT_TOPIC, combined_message)
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
