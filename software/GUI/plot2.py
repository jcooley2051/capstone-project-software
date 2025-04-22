import csv
import json
import subprocess
import threading
from datetime import datetime, timedelta
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from functools import partial
import matplotlib.dates as mdates

# --- Configuration ---
# Constants for file paths, MQTT settings, data time window, and node/metric config.
CSV_FILE = "/home/admin/Documents/capstone-project-software/software/measurements.csv"
MQTT_BROKER = "localhost"
MQTT_PORT = 1337
INPUT_TOPIC = "reading/formatted"
WINDOW_SECONDS = 150  # Show the last 2.5 minutes of data on the plot
NODES = ["PL", "SC", "SP"]  # Node identifiers
METRICS = ["temperature", "humidity", "ambient_light", "particle_count", "vibration"]  # Sensor types
NODE_COLORS = {"PL": "tab:blue", "SC": "tab:green", "SP": "tab:red"}  # Assign consistent colors to each node

# Define Y-axis bounds for each metric (used if autoscale is off)
Y_BOUNDS = {
    "temperature": (10, 40),
    "humidity": (0, 100),
    "ambient_light": (0, 100),
    "particle_count": (0, 100),
    "vibration": (0, 4),
}

# Mapping from metric to CSV header name
CSV_HEADERS = {
    "temperature": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "ambient_light": "Ambient Light (lux)",
    "particle_count": "Particle Count",
    "vibration": "Vibration",
}

# --- State ---
# Initialize the main program state: metric data storage, UI flags, and locking mechanism.
metric_data = {metric: {node: deque() for node in NODES} for metric in METRICS}  # Time-series data
show_node = {node: True for node in NODES}  # Whether each node is currently shown
selected_metric = "temperature"  # Default metric shown at start
paused = False  # Plot pause toggle
autoscale_y = False  # Y-axis autoscaling flag
vibration_lock = threading.Lock()  # Thread-safe lock for shared data
axes_locked = False  # Prevent auto-reset when user zooms/pans

# --- Load CSV Data ---
# Populate the plot with existing CSV data at startup.
def load_initial_data():
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    node = row["Node"]
                    timestamp = datetime.fromisoformat(row["Timestamp"])
                    for metric in METRICS:
                        csv_col = CSV_HEADERS.get(metric)
                        value_str = row.get(csv_col)
                        if value_str:
                            value = float(value_str)
                            with vibration_lock:
                                metric_data[metric][node].append((timestamp, value))
                except Exception:
                    continue  # Skip problematic rows
        trim_old_data()  # Ensure no stale data is left
    except FileNotFoundError:
        print(f"{CSV_FILE} not found. Starting with empty data.")

# --- Trim Old Data ---
# Keep only recent data within the specified time window
def trim_old_data():
    now = datetime.now()
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)
    for metric in METRICS:
        for dq in metric_data[metric].values():
            while dq and dq[0][0] < cutoff:
                dq.popleft()

# --- MQTT Listener ---
# Listen to real-time MQTT messages and append them to the appropriate buffers.
def listen_for_mqtt():
    print("Starting MQTT listener...")
    command = ["mosquitto_sub", "-h", MQTT_BROKER, "-p", str(MQTT_PORT), "-t", INPUT_TOPIC, '-u', 'hackerfab2025', '-P', 'osu2025']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    for line in proc.stdout:
        try:
            msg = json.loads(line.strip())
            overall_time = datetime.fromisoformat(msg.get("time", datetime.now().isoformat()))
            for node_key in ["PL_data", "SC_data", "SP_data"]:
                node = node_key.split("_")[0]
                node_data = msg.get(node_key, {})
                for metric in METRICS:
                    value = node_data.get(metric)
                    if value is not None:
                        try:
                            value = float(str(value).replace(" g", ""))
                            with vibration_lock:
                                metric_data[metric][node].append((overall_time, value))
                        except:
                            continue
            trim_old_data()
        except Exception as e:
            print(f"[ERROR] {e} | Raw line: {line.strip()}")

# --- Plot Update ---
# Called once per animation frame to redraw the current plot.
def update_plot(frame):
    if paused or axes_locked:
        return  # Skip updating if paused or if user has locked the axes

    ax.cla()  # Clear the current axes
    now = datetime.now()
    window_start = now - timedelta(seconds=WINDOW_SECONDS)

    with vibration_lock:
        for node in NODES:
            if not show_node[node]:
                continue
            dq = metric_data[selected_metric][node]
            trimmed = [(t, v) for (t, v) in dq if t >= window_start]
            if not trimmed:
                continue

            # Break into segments if there's a time gap in the data
            segments = []
            current_segment = [trimmed[0]]
            for i in range(1, len(trimmed)):
                if (trimmed[i][0] - trimmed[i - 1][0]).total_seconds() > 5:
                    segments.append(current_segment)
                    current_segment = [trimmed[i]]
                else:
                    current_segment.append(trimmed[i])
            if current_segment:
                segments.append(current_segment)

            # Plot each continuous segment
            for idx, segment in enumerate(segments):
                times, values = zip(*segment)
                ax.plot(times, values, label=node if idx == 0 else "", color=NODE_COLORS[node])

    # Set labels and axis limits
    ax.set_title(f"Live {selected_metric.replace('_', ' ').title()} Readings")
    ax.set_xlabel("Time")
    ax.set_ylabel(selected_metric.replace("_", " ").title())
    ax.set_xlim(window_start, now)

    # Y-axis scaling: either fixed or autoscale
    if autoscale_y:
        ax.relim()
        ax.autoscale_view(scaley=True)
    else:
        lower, upper = Y_BOUNDS.get(selected_metric, (0, 1))
        ax.set_ylim(lower, upper)

    # Add legend only if there's at least one line
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="upper right")

    # Format time display on x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
    fig.autofmt_xdate(rotation=30)
    ax.grid(True)

# --- Button Handlers ---
# Basic interaction functions for closing the plot, toggling nodes, etc.
def on_close(event):
    plt.close(fig)

def toggle_autoscale(event):
    global autoscale_y
    global axes_locked
    autoscale_y = not autoscale_y  # Toggle autoscale
    axes_locked = False  # Unlock axes if user toggles this

def toggle_node(node, event):
    global axes_locked
    show_node[node] = not show_node[node]  # Show/hide the selected node
    axes_locked = False  # Unlock axes when node visibility changes

def set_metric(metric, event):
    global selected_metric
    global axes_locked
    axes_locked = False  # Unlock axes if user switches metric
    selected_metric = metric  # Change currently viewed metric

def on_user_interact(event):
    global axes_locked
    if event.inaxes != ax:
        return  # Ignore clicks outside the main plot
    axes_locked = True  # Prevent automatic axis reset after user zoom/pans

# --- Main ---
# Start the program: load CSV data, start MQTT thread, set up the plot and buttons.
load_initial_data()

mqtt_thread = threading.Thread(target=listen_for_mqtt, daemon=True)
mqtt_thread.start()

fig, ax = plt.subplots()
fig.canvas.manager.set_window_title('Node Plots')
plt.subplots_adjust(bottom=0.2, left=0.25)
fig.canvas.mpl_connect("button_release_event", on_user_interact)
fig.canvas.mpl_connect("scroll_event", on_user_interact)

# --- Buttons ---
# Create buttons on the side and bottom of the plot
button_height = 0.08
button_width = 0.15
spacing = 0.1
start_y = 0.75

# Side buttons for selecting the metric
metric_buttons = {}
for idx, metric in enumerate(METRICS):
    btn_ax = plt.axes([0.03, start_y - idx * spacing, button_width, button_height])
    btn = Button(btn_ax, metric.replace("_", " ").title())
    btn.label.set_fontsize(10)
    btn.on_clicked(partial(set_metric, metric))
    metric_buttons[metric] = btn

# Bottom buttons for toggles and control actions
control_spacing = 0.14
control_start_x = 0.25
btn_axes = {
    "close": plt.axes([control_start_x + control_spacing * 0, 0.01, 0.13, button_height]),
    "autoscale_toggle": plt.axes([control_start_x + control_spacing * 1, 0.01, 0.13, button_height]),
    "toggle_pl": plt.axes([control_start_x + control_spacing * 2, 0.01, 0.13, button_height]),
    "toggle_sc": plt.axes([control_start_x + control_spacing * 3, 0.01, 0.13, button_height]),
    "toggle_sp": plt.axes([control_start_x + control_spacing * 4, 0.01, 0.13, button_height]),
}

# Initialize and bind buttons
btn_close = Button(btn_axes["close"], "Close")
btn_autoscale = Button(btn_axes["autoscale_toggle"], "Auto/Reset Y")
btn_pl = Button(btn_axes["toggle_pl"], "Toggle PL")
btn_sc = Button(btn_axes["toggle_sc"], "Toggle SC")
btn_sp = Button(btn_axes["toggle_sp"], "Toggle SP")

btn_close.on_clicked(on_close)
btn_autoscale.on_clicked(toggle_autoscale)
btn_pl.on_clicked(partial(toggle_node, "PL"))
btn_sc.on_clicked(partial(toggle_node, "SC"))
btn_sp.on_clicked(partial(toggle_node, "SP"))

# Start the animation loop for continuous plot updates
ani = animation.FuncAnimation(fig, update_plot, interval=1000, cache_frame_data=False)

# --- Fullscreen Toggle ---
Resize the window to fill the screen for a better user experience
mng = plt.get_current_fig_manager()
screen_width = mng.window.winfo_screenwidth()
screen_height = mng.window.winfo_screenheight() - 50
mng.window.geometry(f"{screen_width}x{screen_height}+0+0")

plt.show(block=True)
