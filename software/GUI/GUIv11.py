import os
import sys
import signal
import tkinter as T
from tkinter import ttk
import json
import subprocess
from datetime import date as D
from time import sleep
import threading

# create "root" widget
root = T.Tk()
#root.attributes("-fullscreen", True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight() - 50
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.title('Hackerfab Monitoring System')

parent_pid = int(sys.argv[1]) if len(sys.argv) > 1 else None

# MQTT configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = '1337'
INPUT_TOPIC = 'analysis/results'
MQTT_USERNAME = 'hackerfab2025'
MQTT_PASSWORD = 'osu2025'

# Sensor configuration
PL_SENSORS = ('temperature',
              'humidity',
              'ambient_light',
              'vibration')

SC_SENSORS = ('temperature',
              'humidity',
              'particle_count',
              'vibration')

SP_SENSORS = ('temperature',
              'humidity',
              'ambient_light')

STATIONS = {'PL_data': PL_SENSORS,
            'SC_data': SC_SENSORS,
            'SP_data': SP_SENSORS}

def update_vars(root, packet, stringVars, stations):
    try:
        time_str = packet['time']
        time_formatted = time_str.split()[1] if ' ' in time_str else time_str
        stringVars['TB']['time'].set(time_formatted[11:])
    except Exception:
        stringVars['TB']['time'].set('Invalid')

    stringVars['TB']['date'].set(D.today())

    for station, sensors in stations.items():
        for sensor in sensors:
            if sensor in packet[station]:
                stringVars[station][sensor].set(packet[station][sensor])
        if 'status' in packet[station]:
            stringVars[station]['status'].set(packet[station]['status'])

    root.update_idletasks()

def listen_to_topic(root, topic, stringVars, stations):
    print(f'Listening to topic: {topic}')
    command = [
        'mosquitto_sub',
        '-h', MQTT_BROKER,
        '-p', MQTT_PORT,
        '-u', MQTT_USERNAME,
        '-P', MQTT_PASSWORD,
        '-t', topic
    ]

    trying_to_connect = True
    while trying_to_connect:
        try:
            with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
                for line in proc.stdout:
                    line = line.strip()
                    try:
                        packet = json.loads(line)
                        update_vars(root, packet, stringVars, stations)
                        for station, sensors in stations.items():
                            for sensor in sensors:
                                packet[station][sensor] = None
                        packet['time'] = None
                    except ValueError:
                        print(f'Invalid data received on topic "{topic}": {line}')
                trying_to_connect = False
        except Exception as e:
            print(f'Error in listening to topic {topic}: {e}')

TB_time = T.StringVar()
TB_date = T.StringVar()

toolbar_vars = {'time': TB_time,
                'date': TB_date}

PL_temperature = T.StringVar()
PL_humidity = T.StringVar()
PL_ambient_light = T.StringVar()
PL_vibration = T.StringVar()
PL_status = T.StringVar()

photolithography_vars = {'temperature': PL_temperature,
                         'humidity': PL_humidity,
                         'ambient_light': PL_ambient_light,
                         'vibration': PL_vibration,
                         'status': PL_status}

SC_temperature = T.StringVar()
SC_humidity = T.StringVar()
SC_particle_count = T.StringVar()
SC_vibration = T.StringVar()
SC_status = T.StringVar()

spin_coating_vars = {'temperature': SC_temperature,
                     'humidity': SC_humidity,
                     'particle_count': SC_particle_count,
                     'vibration': SC_vibration,
                     'status': SC_status}

SP_temperature = T.StringVar()
SP_humidity = T.StringVar()
SP_ambient_light = T.StringVar()
SP_status = T.StringVar()

sputtering_vars = {'temperature': SP_temperature,
                   'humidity': SP_humidity,
                   'ambient_light': SP_ambient_light,
                   'status': SP_status}

STRINGVARS = {'TB': toolbar_vars,
              'PL_data': photolithography_vars,
              'SC_data': spin_coating_vars,
              'SP_data': sputtering_vars}

toolbar = ttk.Frame(root, padding=10)
stations = ttk.Frame(root, padding=10)

# Add toolbar widgets
ttk.Label(toolbar, text='Hackerfab', font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky='w')
ttk.Label(toolbar, text='OSU', font=('Arial', 14)).grid(row=0, column=1, sticky='w', padx=(10, 30))

ttk.Label(toolbar, text='Time:').grid(row=0, column=6, sticky='e', padx=(10, 0))
ttk.Label(toolbar, textvariable=STRINGVARS['TB']['time']).grid(row=0, column=7, sticky='w', )

ttk.Label(toolbar, text='Date:').grid(row=0, column=8, sticky='e', padx=(20, 0))
ttk.Label(toolbar, textvariable=STRINGVARS['TB']['date']).grid(row=0, column=9, sticky='w')

def launch_child_script():
    try:
        subprocess.Popen(['python3', '/home/admin/Documents/capstone-project-software/software/GUI/plot2.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Child script launched.")
    except Exception as e:
        print(f"Failed to launch script: {e}")

ttk.Button(toolbar, text='Reading Graphs', command=launch_child_script).grid(row=0, column=14, padx=(40, 0))

def make_station_frame(parent, title, sensor_dict, script_path, script_args=None):
    def on_click(event):
        try:
            command = ['python3', script_path]
            if script_args:
                command += script_args
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Launched script: {' '.join(command)}")
        except Exception as e:
            print(f"Failed to launch {script_path}: {e}")

    frame = ttk.LabelFrame(parent, text=title, padding=10)
    row = 0
    for sensor, var in sensor_dict.items():
        if sensor != 'status':
            label1 = ttk.Label(frame, text=f'{sensor.replace("_", " ").title()}:')
            label2 = ttk.Label(frame, textvariable=var)
            style_kwargs = {}
            label1.grid(row=row, column=0, sticky='e', padx=5, pady=2)
            label2.grid(row=row, column=1, sticky='w', padx=5, pady=2)
            label1.configure(**style_kwargs)
            label2.configure(**style_kwargs)
            label1.bind("<Button-1>", on_click)
            label2.bind("<Button-1>", on_click)
            row += 1
    status_label = ttk.Label(frame, text='Status:', font=('Arial', 10, 'bold'))
    status_value = ttk.Label(frame, textvariable=sensor_dict['status'])
    status_label.grid(row=row, column=0, sticky='e', padx=5, pady=(10, 2))
    status_value.grid(row=row, column=1, sticky='w', padx=5, pady=(10, 2))
    status_label.bind("<Button-1>", on_click)
    status_value.bind("<Button-1>", on_click)
    frame.bind("<Button-1>", on_click)
    return frame

PL_frame = make_station_frame(stations, 'Photolithography', STRINGVARS['PL_data'], '/home/admin/Documents/capstone-project-software/software/GUI/node-plot.py', ['PL'])
SC_frame = make_station_frame(stations, 'Spin Coating', STRINGVARS['SC_data'], '/home/admin/Documents/capstone-project-software/software/GUI/node-plot.py', ['SC'])
SP_frame = make_station_frame(stations, 'Sputtering', STRINGVARS['SP_data'], '/home/admin/Documents/capstone-project-software/software/GUI/node-plot.py', ['SP'])

toolbar.grid(row=0, column=0, sticky='ew')
stations.grid(row=1, column=0, sticky='nsew')

PL_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
SC_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
SP_frame.grid(row=0, column=2, padx=10, pady=10, sticky='nsew')

stations.columnconfigure(0, weight=1)
stations.columnconfigure(1, weight=1)
stations.columnconfigure(2, weight=1)

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

STRINGVARS['PL_data']['status'].set('STATUS')
STRINGVARS['SC_data']['status'].set('STATUS')
STRINGVARS['SP_data']['status'].set('STATUS')

listener_thread = threading.Thread(target=listen_to_topic, args=(root, INPUT_TOPIC, STRINGVARS, STATIONS), daemon=True)
listener_thread.start()

# Save Data Button
save_button = ttk.Button(root, text="Save Data", command=lambda: subprocess.Popen(['python3', '/home/admin/Documents/capstone-project-software/software/GUI/save_data.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE))
save_button.grid(row=2, column=0, pady=(10, 30))

def kill_parent():
    if parent_pid:
        try:
            os.kill(parent_pid, signal.SIGINT)
            root.destroy()
        except Exception as e:
            print(f"Failed to kill parent process: {e}")

exit_button = ttk.Button(root, text="Exit All", command=kill_parent)
exit_button.grid(row=3, column=0, pady=(10, 50))


root.mainloop()
