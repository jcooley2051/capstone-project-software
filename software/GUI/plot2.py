# import csv
# import json
# import subprocess
# import threading
# from datetime import datetime, timedelta
# from collections import deque
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# from matplotlib.widgets import Button
# from functools import partial
# import matplotlib.dates as mdates
#
# # --- Configuration ---
# CSV_FILE = "measurements.csv"
# MQTT_BROKER = "localhost"
# MQTT_PORT = 1337
# INPUT_TOPIC = "reading/formatted"
# WINDOW_SECONDS = 150  # 2.5 minutes
# NODES = ["PL", "SC", "SP"]
# METRICS = ["temperature", "humidity", "ambient_light", "particle_count", "vibration"]
# NODE_COLORS = {"PL": "tab:blue", "SC": "tab:green", "SP": "tab:red"}
#
# # Y-axis bounds for each metric
# Y_BOUNDS = {
#     "temperature": (10, 40),
#     "humidity": (0, 100),
#     "ambient_light": (0, 100),
#     "particle_count": (0, 100),
#     "vibration": (0, 4),
# }
#
# # --- State ---
# metric_data = {metric: {node: deque() for node in NODES} for metric in METRICS}
# show_node = {node: True for node in NODES}
# selected_metric = "vibration"
# paused = False
# autoscale_y = False
# vibration_lock = threading.Lock()
#
# # --- Load CSV Data ---
# def load_initial_data():
#     try:
#         with open(CSV_FILE, newline='', encoding='utf-8') as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 try:
#                     node = row["Node"]
#                     timestamp = datetime.fromisoformat(row["Timestamp"])
#                     for metric in METRICS:
#                         value_str = row.get(metric.replace("_", " ").title() + " (g)" if metric == "vibration" else metric.replace("_", " ").title())
#                         if value_str:
#                             value = float(value_str)
#                             with vibration_lock:
#                                 metric_data[metric][node].append((timestamp, value))
#                 except Exception:
#                     continue
#         trim_old_data()
#     except FileNotFoundError:
#         print(f"{CSV_FILE} not found. Starting with empty data.")
#
# # --- Trim Old Data ---
# def trim_old_data():
#     now = datetime.now()
#     cutoff = now - timedelta(seconds=WINDOW_SECONDS)
#     for metric in METRICS:
#         for dq in metric_data[metric].values():
#             while dq and dq[0][0] < cutoff:
#                 dq.popleft()
#
# # --- MQTT Listener ---
# def listen_for_mqtt():
#     print("Starting MQTT listener...")
#     command = ["mosquitto_sub", "-h", MQTT_BROKER, "-p", str(MQTT_PORT), "-t", INPUT_TOPIC]
#     proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
#
#     for line in proc.stdout:
#         try:
#             msg = json.loads(line.strip())
#             overall_time = datetime.fromisoformat(msg.get("time", datetime.now().isoformat()))
#             for node_key in ["PL_data", "SC_data", "SP_data"]:
#                 node = node_key.split("_")[0]
#                 node_data = msg.get(node_key, {})
#                 for metric in METRICS:
#                     value = node_data.get(metric)
#                     if value is not None:
#                         try:
#                             value = float(str(value).replace(" g", ""))
#                             with vibration_lock:
#                                 metric_data[metric][node].append((overall_time, value))
#                         except:
#                             continue
#             trim_old_data()
#         except Exception as e:
#             print(f"[ERROR] {e} | Raw line: {line.strip()}")
#
# # --- Plot Update ---
# def update_plot(frame):
#     if paused:
#         return
#
#     ax.clear()
#     now = datetime.now()
#     window_start = now - timedelta(seconds=WINDOW_SECONDS)
#
#     with vibration_lock:
#         for node in NODES:
#             if not show_node[node]:
#                 continue
#             dq = metric_data[selected_metric][node]
#             trimmed = [(t, v) for (t, v) in dq if t >= window_start]
#             if not trimmed:
#                 continue
#
#             segments = []
#             current_segment = [trimmed[0]]
#             for i in range(1, len(trimmed)):
#                 if (trimmed[i][0] - trimmed[i - 1][0]).total_seconds() > 5:
#                     segments.append(current_segment)
#                     current_segment = [trimmed[i]]
#                 else:
#                     current_segment.append(trimmed[i])
#             if current_segment:
#                 segments.append(current_segment)
#
#             for idx, segment in enumerate(segments):
#                 times, values = zip(*segment)
#                 ax.plot(times, values, label=node if idx == 0 else "", color=NODE_COLORS[node])
#
#     ax.set_title(f"Live {selected_metric.replace('_', ' ').title()} Readings")
#     ax.set_xlabel("Time")
#     ax.set_ylabel(selected_metric.replace("_", " ").title())
#     ax.set_xlim(window_start, now)
#     if autoscale_y:
#         ax.relim()
#         ax.autoscale_view(scaley=True)
#     else:
#         lower, upper = Y_BOUNDS.get(selected_metric, (0, 1))
#         ax.set_ylim(lower, upper)
#     if ax.get_legend_handles_labels()[0]:
#         ax.legend(loc="upper right")
#     ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
#     fig.autofmt_xdate(rotation=30)
#     ax.grid(True)
#
# # --- Button Handlers ---
# def on_close(event):
#     plt.close(fig)
#
# def on_autoscale(event):
#     global autoscale_y
#     autoscale_y = True
#
# def on_reset(event):
#     global autoscale_y
#     autoscale_y = False
#
# def toggle_node(node, event):
#     show_node[node] = not show_node[node]
#
# def set_metric(metric, event):
#     global selected_metric
#     selected_metric = metric
#
# # --- Main ---
# load_initial_data()
#
# mqtt_thread = threading.Thread(target=listen_for_mqtt, daemon=True)
# mqtt_thread.start()
#
# fig, ax = plt.subplots()
# plt.subplots_adjust(bottom=0.2, left=0.25)
#
# # --- Buttons ---
# button_height = 0.08
# button_width = 0.15
# spacing = 0.1
# start_y = 0.85
#
# # Side row (metric selectors)
# metric_buttons = {}
# for idx, metric in enumerate(METRICS):
#     btn_ax = plt.axes([0.03, start_y - idx * spacing, button_width, button_height])
#     btn = Button(btn_ax, metric.replace("_", " ").title())
#     btn.label.set_fontsize(10)
#     btn.on_clicked(partial(set_metric, metric))
#     metric_buttons[metric] = btn
#
# # Bottom row (controls)
# control_spacing = 0.13
# control_start_x = 0.25
# btn_axes = {
#     "close": plt.axes([control_start_x + control_spacing * 0, 0.01, 0.1, button_height]),
#     "autoscale": plt.axes([control_start_x + control_spacing * 1, 0.01, 0.1, button_height]),
#     "reset": plt.axes([control_start_x + control_spacing * 2, 0.01, 0.1, button_height]),
#     "toggle_pl": plt.axes([control_start_x + control_spacing * 3, 0.01, 0.1, button_height]),
#     "toggle_sc": plt.axes([control_start_x + control_spacing * 4, 0.01, 0.1, button_height]),
#     "toggle_sp": plt.axes([control_start_x + control_spacing * 5, 0.01, 0.1, button_height]),
# }
#
# btn_close = Button(btn_axes["close"], "Close")
# btn_autoscale = Button(btn_axes["autoscale"], "Auto Y")
# btn_reset = Button(btn_axes["reset"], "Reset Y")
# btn_pl = Button(btn_axes["toggle_pl"], "Toggle PL")
# btn_sc = Button(btn_axes["toggle_sc"], "Toggle SC")
# btn_sp = Button(btn_axes["toggle_sp"], "Toggle SP")
#
# btn_close.on_clicked(on_close)
# btn_autoscale.on_clicked(on_autoscale)
# btn_reset.on_clicked(on_reset)
# btn_pl.on_clicked(partial(toggle_node, "PL"))
# btn_sc.on_clicked(partial(toggle_node, "SC"))
# btn_sp.on_clicked(partial(toggle_node, "SP"))
#
# ani = animation.FuncAnimation(fig, update_plot, interval=1000, cache_frame_data=False)
# plt.show(block=True)
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
CSV_FILE = "measurements.csv"
MQTT_BROKER = "localhost"
MQTT_PORT = 1337
INPUT_TOPIC = "reading/formatted"
WINDOW_SECONDS = 150  # 2.5 minutes
NODES = ["PL", "SC", "SP"]
METRICS = ["temperature", "humidity", "ambient_light", "particle_count", "vibration"]
NODE_COLORS = {"PL": "tab:blue", "SC": "tab:green", "SP": "tab:red"}

# Y-axis bounds for each metric
Y_BOUNDS = {
    "temperature": (10, 40),
    "humidity": (0, 100),
    "ambient_light": (0, 100),
    "particle_count": (0, 100),
    "vibration": (0, 4),
}

# CSV header mapping
CSV_HEADERS = {
    "temperature": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "ambient_light": "Ambient Light (lux)",
    "particle_count": "Particle Count",
    "vibration": "Vibration",
}

# --- State ---
metric_data = {metric: {node: deque() for node in NODES} for metric in METRICS}
show_node = {node: True for node in NODES}
selected_metric = "vibration"
paused = False
autoscale_y = False
vibration_lock = threading.Lock()

# --- Load CSV Data ---
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
                    continue
        trim_old_data()
    except FileNotFoundError:
        print(f"{CSV_FILE} not found. Starting with empty data.")

# --- Trim Old Data ---
def trim_old_data():
    now = datetime.now()
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)
    for metric in METRICS:
        for dq in metric_data[metric].values():
            while dq and dq[0][0] < cutoff:
                dq.popleft()

# --- MQTT Listener ---
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
def update_plot(frame):
    if paused:
        return

    ax.clear()
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

            for idx, segment in enumerate(segments):
                times, values = zip(*segment)
                ax.plot(times, values, label=node if idx == 0 else "", color=NODE_COLORS[node])

    ax.set_title(f"Live {selected_metric.replace('_', ' ').title()} Readings")
    ax.set_xlabel("Time")
    ax.set_ylabel(selected_metric.replace("_", " ").title())
    ax.set_xlim(window_start, now)
    if autoscale_y:
        ax.relim()
        ax.autoscale_view(scaley=True)
    else:
        lower, upper = Y_BOUNDS.get(selected_metric, (0, 1))
        ax.set_ylim(lower, upper)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="upper right")

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
    fig.autofmt_xdate(rotation=30)
    ax.grid(True)

# --- Button Handlers ---
def on_close(event):
    plt.close(fig)

def on_autoscale(event):
    global autoscale_y
    autoscale_y = True

def on_reset(event):
    global autoscale_y
    autoscale_y = False

def toggle_node(node, event):
    show_node[node] = not show_node[node]

def set_metric(metric, event):
    global selected_metric
    selected_metric = metric

# --- Main ---
load_initial_data()

mqtt_thread = threading.Thread(target=listen_for_mqtt, daemon=True)
mqtt_thread.start()

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2, left=0.25)

# --- Buttons ---
button_height = 0.08
button_width = 0.15
spacing = 0.1
start_y = 0.85

# Side row (metric selectors)
metric_buttons = {}
for idx, metric in enumerate(METRICS):
    btn_ax = plt.axes([0.03, start_y - idx * spacing, button_width, button_height])
    btn = Button(btn_ax, metric.replace("_", " ").title())
    btn.label.set_fontsize(10)
    btn.on_clicked(partial(set_metric, metric))
    metric_buttons[metric] = btn

# Bottom row (controls)
control_spacing = 0.13
control_start_x = 0.25
btn_axes = {
    "close": plt.axes([control_start_x + control_spacing * 0, 0.01, 0.1, button_height]),
    "autoscale": plt.axes([control_start_x + control_spacing * 1, 0.01, 0.1, button_height]),
    "reset": plt.axes([control_start_x + control_spacing * 2, 0.01, 0.1, button_height]),
    "toggle_pl": plt.axes([control_start_x + control_spacing * 3, 0.01, 0.1, button_height]),
    "toggle_sc": plt.axes([control_start_x + control_spacing * 4, 0.01, 0.1, button_height]),
    "toggle_sp": plt.axes([control_start_x + control_spacing * 5, 0.01, 0.1, button_height]),
}

btn_close = Button(btn_axes["close"], "Close")
btn_autoscale = Button(btn_axes["autoscale"], "Auto Y")
btn_reset = Button(btn_axes["reset"], "Reset Y")
btn_pl = Button(btn_axes["toggle_pl"], "Toggle PL")
btn_sc = Button(btn_axes["toggle_sc"], "Toggle SC")
btn_sp = Button(btn_axes["toggle_sp"], "Toggle SP")

btn_close.on_clicked(on_close)
btn_autoscale.on_clicked(on_autoscale)
btn_reset.on_clicked(on_reset)
btn_pl.on_clicked(partial(toggle_node, "PL"))
btn_sc.on_clicked(partial(toggle_node, "SC"))
btn_sp.on_clicked(partial(toggle_node, "SP"))

ani = animation.FuncAnimation(fig, update_plot, interval=1000, cache_frame_data=False)
plt.show(block=True)
