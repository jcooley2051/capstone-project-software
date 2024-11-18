import csv
from datetime import datetime, timedelta

# Lists to store data
measurements = []
out_of_range = []
contextual_measurements = []

# Acceptable Ranges
acceptable_temp_range = (18, 30)  # Example: 18°C to 30°C
acceptable_humid_range = (30, 70)  # Example: 30% to 70%

# CSV File for Storing Measurements
CSV_FILE = "measurements.csv"
OUT_OF_RANGE_FILE = "out_of_range.csv"  # File to log out-of-range values with context

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
        writer.writerow([measurement['temp'], measurement['humid'], measurement['time'].strftime('%Y-%m-%d %H:%M:%S')])

# Save Out-of-Range Measurement with Context to CSV
def save_out_of_range(measurement, context):
    with open(OUT_OF_RANGE_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            measurement['temp'],
            measurement['humid'],
            measurement['time'].strftime('%Y-%m-%d %H:%M:%S'),
            context
        ])

# Add and Analyze Measurement
def add_measurement(temp, humid, time):
    measurement = {"temp": temp, "humid": humid, "time": time}
    measurements.append(measurement)
    save_to_csv(measurement)

    # Check if measurement is out of range
    if not (acceptable_temp_range[0] <= temp <= acceptable_temp_range[1]) or not (acceptable_humid_range[0] <= humid <= acceptable_humid_range[1]):
        out_of_range.append(measurement)
        print(f"Out-of-range detected: {measurement}")

        # Capture Contextual Measurements
        start_time = time - timedelta(seconds=30)
        end_time = time + timedelta(seconds=30)
        context = []
        for m in measurements:
            if start_time <= m['time'] <= end_time:
                contextual_measurements.append(m)
                context.append(f"Temp: {m['temp']}, Humid: {m['humid']}, Time: {m['time'].strftime('%Y-%m-%d %H:%M:%S')}")

        # Save out-of-range measurement with context
        save_out_of_range(measurement, "; ".join(context))

# Public Function for Formatter to Call
def process_input(temp, humid, timestamp):
    """
    Accepts temperature, humidity, and timestamp from the formatter script.
    """
    time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    add_measurement(temp, humid, time)

# Initialize CSV if starting fresh
initialize_csv()
