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
acceptable_light_range = (0, 30)       # Ambient light in lux
acceptable_particle_range = (0, 1000)  # Particle count

# New vibration limits (scalar)
VIBRATION_MIN = 0.0
VIBRATION_MAX = 0.5

# Sensor extreme values
BME280_TEMP_MAX = 85    
BME280_TEMP_MIN = -40   
HUMIDITY_MAX = 100      
HUMIDITY_MIN = 0        
VEML7700_MAX_LIGHT = 120000
IH_PMC_001_MAX = 1000   

# CSV Files (including Node)
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"
CONTEXT_FILE = "context_data.csv"

# Global in-memory cache for 5-hour measurements.
measurements_cache = []

# Global list to store error events in a 5-minute buffer.
fiveminbuff = []

def safe_str(val):
    return str(val) if val is not None else ""

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
                safe_str(m.get("node")),
                safe_str(m.get("temperature")),
                safe_str(m.get("humidity")),
                safe_str(m.get("ambient_light")),
                safe_str(m.get("particle_count")),
                safe_str(m.get("vibration")),
                safe_str(m.get("time"))
            ])

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

def check_early_warning(measurement):
    if len(measurements_cache) < 3:
        return
    sorted_measurements = sorted(measurements_cache, key=lambda m: datetime.fromisoformat(m['time']))
    valid_vib = [m for m in sorted_measurements if isinstance(m.get("vibration"), (int, float))]
    if len(valid_vib) < 3:
        return
    recent_vib = valid_vib[-3:]
    node_id = measurement.get("node", "Unknown")
    if recent_vib[0]["vibration"] < recent_vib[1]["vibration"] < recent_vib[2]["vibration"]:
        current_vib = measurement.get("vibration")
        if isinstance(current_vib, (int, float)):
            warning_margin = 0.05
            if current_vib >= VIBRATION_MAX - warning_margin:
                print(f"Early Warning: {node_id} vibration reading is increasing and nearing its bound. Current value: {current_vib}")

def analyze_and_process_node(measurement):
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

    for event in fiveminbuff.copy():
        if event['error_time'] < current_time <= event['deadline']:
            save_context_data(measurement, "Surrounding Errors (post)")
        if current_time > event['deadline']:
            fiveminbuff.remove(event)
    
    check_early_warning(measurement)
    publish_to_mqtt(OUTPUT_TOPIC, measurement)

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
                try:
                    message = json.loads(line)
                    if "node" in message:
                        analyze_and_process_node(message)
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
