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

# --- Configuration Section ---
CSV_FILE = "/home/admin/Documents/capstone-project-software/software/measurements.csv"  # Path to the local CSV file for initial data load
WINDOW_SECONDS = 60  # Number of seconds to display on the graph (rolling window)
MQTT_BROKER = "localhost"  # MQTT broker address
MQTT_PORT = 1337  # MQTT broker port
INPUT_TOPIC = "reading/formatted"  # MQTT topic for incoming data

# Define which metrics each node type sends
NODE_METRICS = {
    "PL": ["temperature", "humidity", "ambient_light", "vibration"],
    "SC": ["temperature", "humidity", "particle_count", "vibration"],
    "SP": ["temperature", "humidity", "ambient_light"],
}

# Human-readable CSV headers for each metric
CSV_HEADERS = {
    "temperature": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "ambient_light": "Ambient Light (lux)",
    "particle_count": "Particle Count",
    "vibration": "Vibration",
}

# Default Y-axis bounds if autoscale is not used
Y_BOUNDS = {
    "temperature": (10, 40),
    "humidity": (0, 100),
    "ambient_light": (0, 100),
    "particle_count": (0, 100),
    "vibration": (0, 4),
}

# --- Handle Command-Line Arguments ---
# Make sure the user passed in a valid node type (PL, SC, or SP)
if len(sys.argv) < 2 or sys.argv[1] not in NODE_METRICS:
    print("Usage: python script.py <PL|SC|SP>")
    sys.exit(1)

node_type = sys.argv[1]
metrics = NODE_METRICS[node_type]  # Metrics to monitor for this node type
data = {metric: deque() for metric in metrics}  # Stores recent values for each metric
autoscale = False  # Flag to toggle Y-axis autoscaling
axes_locked = {metric: False for metric in metrics}  # Tracks which plots are frozen

# --- CSV Initialization ---
# Load past measurements from CSV to populate the graph initially
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

# Remove old data points that fall outside the visible time window
def trim_old_data():
    cutoff = datetime.now() - timedelta(seconds=WINDOW_SECONDS)
    for dq in data.values():
        while dq and dq[0][0] < cutoff:
            dq.popleft()

# --- MQTT Listener ---
# This function spawns a subprocess to subscribe to the MQTT broker and parse incoming data
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
                        value = float(str(value).replace(" g", ""))  # Clean up value string if needed
                        data[metric].append((overall_time, value))
                    except:
                        continue
            trim_old_data()
        except Exception as e:
            print(f"[ERROR] {e} | Raw line: {line.strip()}")

# --- Plot Update ---
# Called once per frame to redraw the plots
def update(frame):
    now = datetime.now()
    window_start = now - timedelta(seconds=WINDOW_SECONDS)

    for ax, metric in zip(axes, metrics):
        if axes_locked[metric]:
            continue  # Skip updating if user has zoomed/panned manually

        dq = data[metric]
        trimmed = [(t, v) for t, v in dq if t >= window_start]
        if not trimmed:
            continue

        ax.cla()  # Clear previous contents

        # Break the line if the time gap between points is too large (e.g., data dropout)
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

        # Draw each continuous segment
        for segment in segments:
            times, values = zip(*segment)
            ax.plot(times, values, color="tab:blue")

        ax.set_title(metric.replace("_", " ").title(), fontsize=8)
        if not axes_locked[metric]:
            ax.set_xlim(window_start, now)

        if autoscale:
            ax.relim()
            ax.autoscale_view()
        else:
            ax.set_xlim(window_start, now)
            ymin, ymax = Y_BOUNDS.get(metric, (0, 1))
            ax.set_ylim(ymin, ymax)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
        ax.tick_params(axis='x', labelsize=6)
        ax.tick_params(axis='y', labelsize=6)

# --- Button and Event Handlers ---

# Toggle Y-axis autoscaling and reset axis locks
def toggle_autoscale(event):
    global autoscale
    global axes_lock
    autoscale = not autoscale
    for metric in axes_locked:
        axes_locked[metric] = False  # Reset all axes locks

# When user zooms or pans, lock that axis so it won’t get overridden
def on_user_interact(event):
    if event.inaxes not in axes:
        return  # Ignore if click/scroll isn’t on a plot
    for ax, metric in zip(axes, metrics):
        if event.inaxes == ax:
            axes_locked[metric] = True

# Close the plot window
def close_plot(event):
    plt.close()

# --- Plot Initialization ---
load_initial_data()

# Layout setup
cols = 2
rows = math.ceil(len(metrics) / cols)
fig, axes = plt.subplots(rows, cols, figsize=(6, 2.5 * rows))
fig.canvas.manager.set_window_title('Reading Plots')
axes = axes.flatten()[:len(metrics)]  # Trim to the number of metrics we need

# Connect zoom/pan events
fig.canvas.mpl_connect("button_release_event", on_user_interact)
fig.canvas.mpl_connect("scroll_event", on_user_interact)

# Adjust subplot spacing and add control buttons
plt.subplots_adjust(left=0.2, bottom=0.2, hspace=0.6, wspace=0.3)

btn_ax1 = plt.axes([0.3, 0.02, 0.2, 0.06])
btn_ax2 = plt.axes([0.55, 0.02, 0.2, 0.06])
btn_autoscale = Button(btn_ax1, "Auto/Reset Y")
btn_close = Button(btn_ax2, "Close")
btn_autoscale.on_clicked(toggle_autoscale)
btn_close.on_clicked(close_plot)

# Start the MQTT listener on a background thread
mqtt_thread = threading.Thread(target=listen_to_mqtt, daemon=True)
mqtt_thread.start()

# Start the animation loop (updates every second)
ani = animation.FuncAnimation(fig, update, interval=1000)

# Make the plot fullscreen on launch
mng = plt.get_current_fig_manager()
screen_width = mng.window.winfo_screenwidth()
screen_height = mng.window.winfo_screenheight() - 50
mng.window.geometry(f"{screen_width}x{screen_height}+0+0")

# Show the plot window
plt.show()
