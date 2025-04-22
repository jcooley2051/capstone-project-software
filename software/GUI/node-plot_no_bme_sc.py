import sys
import csv
import json
import subprocess
import threading
from datetime import datetime, timedelta
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.animation as animation
import matplotlib.dates as mdates
import math

# Configuration
CSV_FILE = "/home/admin/Documents/capstone-project-software/software/measurements.csv"
WINDOW_SECONDS = 60  # 1 minute
MQTT_BROKER = "localhost"
MQTT_PORT = 1337
INPUT_TOPIC = "reading/formatted"
NODE_METRICS = {
    "PL": ["temperature", "humidity", "ambient_light", "vibration"],
    "SC": ["particle_count", "vibration"],
    "SP": ["temperature", "humidity", "ambient_light"],
}
CSV_HEADERS = {
    "temperature": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "ambient_light": "Ambient Light (lux)",
    "particle_count": "Particle Count",
    "vibration": "Vibration",
}
Y_BOUNDS = {
    "temperature": (10, 40),
    "humidity": (0, 100),
    "ambient_light": (0, 100),
    "particle_count": (0, 100),
    "vibration": (0, 4),
}

# Get node from arguments
if len(sys.argv) < 2 or sys.argv[1] not in NODE_METRICS:
    print("Usage: python script.py <PL|SC|SP>")
    sys.exit(1)

node_type = sys.argv[1]
metrics = NODE_METRICS[node_type]
data = {metric: deque() for metric in metrics}
autoscale = False

# Load CSV data

def load_initial_data():
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Node"] != node_type:
                    continue
                timestamp = datetime.fromisoformat(row["Timestamp"])
                for metric in metrics:
                    val = row.get(CSV_HEADERS[metric])
                    if val:
                        data[metric].append((timestamp, float(val)))
        trim_old_data()
    except FileNotFoundError:
        print(f"{CSV_FILE} not found.")


def trim_old_data():
    cutoff = datetime.now() - timedelta(seconds=WINDOW_SECONDS)
    for dq in data.values():
        while dq and dq[0][0] < cutoff:
            dq.popleft()

def listen_to_mqtt():
    print("Starting MQTT listener...")
    command = ["mosquitto_sub", "-h", MQTT_BROKER, "-p", str(MQTT_PORT), "-t", INPUT_TOPIC, '-u', 'hackerfab2025', '-P', 'osu2025']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    for line in proc.stdout:
        try:
            msg = json.loads(line.strip())
            overall_time = datetime.fromisoformat(msg.get("time", datetime.now().isoformat()))
            node_data = msg.get(f"{node_type}_data", {})
            for metric in metrics:
                value = node_data.get(metric)
                if value is not None:
                    try:
                        value = float(str(value).replace(" g", ""))
                        data[metric].append((overall_time, value))
                    except:
                        continue
            trim_old_data()
        except Exception as e:
            print(f"[ERROR] {e} | Raw line: {line.strip()}")

def update(frame):
    now = datetime.now()
    window_start = now - timedelta(seconds=WINDOW_SECONDS)

    for ax, metric in zip(axes, metrics):
        ax.clear()
        dq = data[metric]
        trimmed = [(t, v) for t, v in dq if t >= window_start]
        if not trimmed:
            continue

        # Segment the data to break the line if the time gap exceeds 5 seconds
        segments = []
        current_segment = [trimmed[0]]

        for i in range(1, len(trimmed)):
            prev_time, _ = trimmed[i - 1]
            curr_time, _ = trimmed[i]
            if (curr_time - prev_time).total_seconds() > 5:
                segments.append(current_segment)
                current_segment = [trimmed[i]]
            else:
                current_segment.append(trimmed[i])
        if current_segment:
            segments.append(current_segment)

        for segment in segments:
            times, values = zip(*segment)
            ax.plot(times, values, color="tab:blue")

        ax.set_title(metric.replace("_", " ").title(), fontsize=8)
        ax.set_xlim(window_start, now)
        if autoscale:
            ax.relim()
            ax.autoscale_view()
        else:
            ymin, ymax = Y_BOUNDS.get(metric, (0, 1))
            ax.set_ylim(ymin, ymax)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
        ax.tick_params(axis='x', labelsize=6)
        ax.tick_params(axis='y', labelsize=6)

def toggle_autoscale(event):
    global autoscale
    autoscale = not autoscale

def close_plot(event):
    plt.close()

# Set up plots
load_initial_data()

cols = 2
rows = math.ceil(len(metrics) / cols)
fig, axes = plt.subplots(rows, cols, figsize=(6, 2.5 * rows))
fig.canvas.manager.set_window_title('Reading Plots')
axes = axes.flatten()[:len(metrics)]
plt.subplots_adjust(left=0.2, bottom=0.2, hspace=0.6, wspace=0.3)

btn_ax1 = plt.axes([0.3, 0.02, 0.2, 0.06])
btn_ax2 = plt.axes([0.55, 0.02, 0.2, 0.06])
btn_autoscale = Button(btn_ax1, "Auto/Reset Y")
btn_close = Button(btn_ax2, "Close")
btn_autoscale.on_clicked(toggle_autoscale)
btn_close.on_clicked(close_plot)

mqtt_thread = threading.Thread(target=listen_to_mqtt, daemon=True)
mqtt_thread.start()

ani = animation.FuncAnimation(fig, update, interval=1000)

# Add fullscreen toggle
mng = plt.get_current_fig_manager()
screen_width = mng.window.winfo_screenwidth()
screen_height = mng.window.winfo_screenheight() - 50
mng.window.geometry(f"{screen_width}x{screen_height}+0+0")

plt.show()
