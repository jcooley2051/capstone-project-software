import tkinter as T
from tkinter import ttk
import json
import subprocess
from datetime import date as D
from time import sleep
import threading

# create "root" widget
root = T.Tk()
root.title('Hackerfab Monitoring System')

# MQTT configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = '1337'
INPUT_TOPIC = 'analysis/results'
MQTT_USERNAME = 'hackerfab2025'
MQTT_PASSWORD = 'osu2025'

# Sensor configuration
"""
Create Python Tuples for each station containing that station's sensor types
~~~~~~TEMPLATE~~~~~~
St_SENSORS = ('sensor_1',
              'sensor_2',
              'sensor_3')
"""
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

"""
Create Python Dictionary containing all stations
~~~~~~TEMPLATE~~~~~~
STATIONS = {'St': St_sensors}
"""
# Note: Keys match those in the MQTT message: "PL_data", "SC_data", "SP_data"
STATIONS = {'PL_data': PL_SENSORS,
            'SC_data': SC_SENSORS,
            'SP_data': SP_SENSORS}

# Function to update StringVars with packet data.
def update_vars(root, packet, stringVars, stations):
    '''Update GUI variables with new sensor readings from packet'''
    # Format time as HH:MM:SS
    try:
        time_str = packet['time']
        time_formatted = time_str.split()[1] if ' ' in time_str else time_str
        stringVars['TB']['time'].set(time_formatted[11:])  # Truncate to HH:MM:SS
    except Exception:
        stringVars['TB']['time'].set('Invalid')

    stringVars['TB']['date'].set(D.today())

    for station, sensors in stations.items():
        # Update each sensor value.
        for sensor in sensors:
            if sensor in packet[station]:
                stringVars[station][sensor].set(packet[station][sensor])
        # Update the status if it is provided in the packet.
        if 'status' in packet[station]:
            stringVars[station]['status'].set(packet[station]['status'])
        
    root.update_idletasks()

def listen_to_topic(root, topic, stringVars, stations):
    '''Listen to the MQTT topic and update the GUI accordingly'''
    print(f'Listening to topic: {topic}')  # Debug message
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
                        # Optionally, reset data in packet if needed.
                        for station, sensors in stations.items():
                            for sensor in sensors:
                                packet[station][sensor] = None 
                        packet['time'] = None
                    except ValueError:
                        print(f'Invalid data received on topic "{topic}": {line}')
                trying_to_connect = False
        except Exception as e:
            print(f'Error in listening to topic {topic}: {e}')

'''
Create tkinter StringVars to store individual values to be displayed.
Combine StringVars into dictionaries to simplify passing to update functions.
'''

# Toolbar StringVars
TB_time = T.StringVar()
TB_date = T.StringVar()

toolbar_vars = {'time': TB_time,
                'date': TB_date}

# Photolithography StringVars
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

# Spin Coating StringVars
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

# Sputtering StringVars
SP_temperature = T.StringVar()
SP_humidity = T.StringVar()
SP_ambient_light = T.StringVar()
SP_status = T.StringVar()

sputtering_vars = {'temperature': SP_temperature,
                   'humidity': SP_humidity,
                   'ambient_light': SP_ambient_light,
                   'status': SP_status}

"""
Create Python Dictionary containing station StringVars.
Keys must match the MQTT message keys: "PL_data", "SC_data", "SP_data".
"""
STRINGVARS = {'TB': toolbar_vars,
              'PL_data': photolithography_vars,
              'SC_data': spin_coating_vars,
              'SP_data': sputtering_vars}

''' Create tkinter frame widgets to organize content widgets '''
# Organize layout using LabelFrames for clarity
toolbar = ttk.Frame(root, padding=10)
stations = ttk.Frame(root, padding=10)

# Add toolbar widgets
ttk.Label(toolbar, text='Hackerfab', font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky='w')
ttk.Label(toolbar, text='OSU', font=('Arial', 14)).grid(row=0, column=1, sticky='w', padx=(10, 30))

ttk.Label(toolbar, text='Time:').grid(row=0, column=6, sticky='e')
ttk.Label(toolbar, textvariable=STRINGVARS['TB']['time']).grid(row=0, column=7, sticky='w')

ttk.Label(toolbar, text='Date:').grid(row=0, column=8, sticky='e')
ttk.Label(toolbar, textvariable=STRINGVARS['TB']['date']).grid(row=0, column=9, sticky='w')

def launch_child_script():
    # Replace "other_script.py" with the path to your script
    try:
        subprocess.Popen(['python3', './GUI/plot2.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Child script launched.")
    except Exception as e:
        print(f"Failed to launch script: {e}")

ttk.Button(toolbar, text='Reading Graphs', command=launch_child_script).grid(row=0, column=10, padx=(20, 0))

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
    frame.bind("<Button-1>", on_click)  # Bind click event to whole frame

    row = 0
    for sensor, var in sensor_dict.items():
        if sensor != 'status':
            ttk.Label(frame, text=f'{sensor.replace("_", " ").title()}:').grid(row=row, column=0, sticky='e', padx=5, pady=2)
            ttk.Label(frame, textvariable=var).grid(row=row, column=1, sticky='w', padx=5, pady=2)
            row += 1

    ttk.Label(frame, text='Status:', font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky='e', padx=5, pady=(10, 2))
    ttk.Label(frame, textvariable=sensor_dict['status']).grid(row=row, column=1, sticky='w', padx=5, pady=(10, 2))

    return frame


# Create station blocks
PL_frame = make_station_frame(stations, 'Photolithography', STRINGVARS['PL_data'], './GUI/node-plot.py', ['PL'])
SC_frame = make_station_frame(stations, 'Spin Coating', STRINGVARS['SC_data'], './GUI/node-plot.py', ['SC'])
SP_frame = make_station_frame(stations, 'Sputtering', STRINGVARS['SP_data'], './softwae/GUI/node-plot.py', ['SP'])



# Grid placement
toolbar.grid(row=0, column=0, sticky='ew')
stations.grid(row=1, column=0, sticky='nsew')

PL_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
SC_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
SP_frame.grid(row=0, column=2, padx=10, pady=10, sticky='nsew')

# Make columns expand evenly
stations.columnconfigure(0, weight=1)
stations.columnconfigure(1, weight=1)
stations.columnconfigure(2, weight=1)

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

# Set initial status values
STRINGVARS['PL_data']['status'].set('STATUS')
STRINGVARS['SC_data']['status'].set('STATUS')
STRINGVARS['SP_data']['status'].set('STATUS')

# Start the MQTT listener in a separate thread.
listener_thread = threading.Thread(target=listen_to_topic, args=(root, INPUT_TOPIC, STRINGVARS, STATIONS), daemon=True)
listener_thread.start()

# Start the Tkinter main event loop

root.mainloop()
