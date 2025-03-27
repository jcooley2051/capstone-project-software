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
    # Update toolbar values
    stringVars['TB']['temperature'].set('PLACEHOLDER')
    stringVars['TB']['humidity'].set('PLACEHOLDER')
    stringVars['TB']['time'].set(packet['time'])
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
TB_temperature = T.StringVar()
TB_humidity = T.StringVar()
TB_time = T.StringVar()
TB_date = T.StringVar()

toolbar_vars = {'temperature': TB_temperature,
                'humidity': TB_humidity,
                'time': TB_time,
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
mainframe = ttk.Frame(root)

# Toolbar frames
toolbar = ttk.Frame(mainframe)
toolbar_watermarks = ttk.Frame(toolbar)
toolbar_tabs = ttk.Frame(toolbar)
toolbar_info = ttk.Frame(toolbar)

# Stations frames
stations = ttk.Frame(mainframe)
station_PL = ttk.Frame(stations)
PL_weather = ttk.Frame(station_PL)
station_SC = ttk.Frame(stations)
SC_weather = ttk.Frame(station_SC)
station_SP = ttk.Frame(stations)
SP_weather = ttk.Frame(station_SP)
status = ttk.Frame(stations)

''' Create content widgets to display data readings '''
# Toolbar content widgets
watermark_HFAB = ttk.Label(toolbar_watermarks, text='Hackerfab')
watermark_OSU = ttk.Label(toolbar_watermarks, text='OSU')
TB_temperature_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['temperature'])
TB_humidity_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['humidity'])
TB_time_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['time'])
TB_date_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['date'])

# Photolithography content widgets
PL_station_label = ttk.Label(station_PL, text='Photolithography')
PL_temperature_label = ttk.Label(PL_weather, textvariable=STRINGVARS['PL_data']['temperature'])
PL_humidity_label = ttk.Label(PL_weather, textvariable=STRINGVARS['PL_data']['humidity'])
PL_ambient_light_label = ttk.Label(station_PL, textvariable=STRINGVARS['PL_data']['ambient_light'])
PL_vibration_label = ttk.Label(station_PL, textvariable=STRINGVARS['PL_data']['vibration'])
PL_status_label = ttk.Label(status, textvariable=STRINGVARS['PL_data']['status'])

# Spin Coating content widgets
SC_station_label = ttk.Label(station_SC, text='Spin Coating')
SC_temperature_label = ttk.Label(SC_weather, textvariable=STRINGVARS['SC_data']['temperature'])
SC_humidity_label = ttk.Label(SC_weather, textvariable=STRINGVARS['SC_data']['humidity'])
SC_particle_count_label = ttk.Label(station_SC, textvariable=STRINGVARS['SC_data']['particle_count'])
SC_vibration_label = ttk.Label(station_SC, textvariable=STRINGVARS['SC_data']['vibration'])
SC_status_label = ttk.Label(status, textvariable=STRINGVARS['SC_data']['status'])

# Sputtering content widgets
SP_station_label = ttk.Label(station_SP, text='Sputtering')
SP_temperature_label = ttk.Label(SP_weather, textvariable=STRINGVARS['SP_data']['temperature'])
SP_humidity_label = ttk.Label(SP_weather, textvariable=STRINGVARS['SP_data']['humidity'])
SP_ambient_light_label = ttk.Label(station_SP, textvariable=STRINGVARS['SP_data']['ambient_light'])
SP_status_label = ttk.Label(status, textvariable=STRINGVARS['SP_data']['status'])

''' Geometry management '''
# Place mainframe in root
mainframe.grid(row=0, column=0, sticky='nsew')

# Layout in mainframe
toolbar.grid(row=0, column=0, sticky='new')
stations.grid(row=1, column=0, sticky='nsew')

# Toolbar sub-frames
toolbar_watermarks.grid(row=0, column=0, sticky='nsew')
toolbar_tabs.grid(row=0, column=1, sticky='nsew')
toolbar_info.grid(row=0, column=2, sticky='nsew')

# Watermarks in toolbar
watermark_HFAB.grid(row=0, column=0, sticky='ew')
watermark_OSU.grid(row=0, column=1, sticky='w')

# Toolbar info widgets
TB_temperature_label.grid(row=0, column=0, sticky='e')
TB_humidity_label.grid(row=0, column=1, sticky='ew')
TB_time_label.grid(row=0, column=2, sticky='ew')
TB_date_label.grid(row=0, column=3, sticky='ew')

# Stations layout
station_PL.grid(row=0, column=0, sticky='nsew')
station_SC.grid(row=0, column=1, sticky='nsew')
station_SP.grid(row=0, column=2, sticky='nsew')
status.grid(row=1, column=0, columnspan=3, sticky='nsew')

# Photolithography station layout
PL_station_label.grid(row=0, column=0, sticky='ns')
PL_weather.grid(row=1, column=0, sticky='nsew')
PL_ambient_light_label.grid(row=2, column=0, sticky='ns')
PL_vibration_label.grid(row=3, column=0, sticky='ns')

# Spin Coating station layout
SC_station_label.grid(row=0, column=0, sticky='ns')
SC_weather.grid(row=1, column=0, sticky='nsew')
SC_particle_count_label.grid(row=2, column=0, sticky='ns')
SC_vibration_label.grid(row=3, column=0, sticky='ns')

# Sputtering station layout
SP_station_label.grid(row=0, column=0, sticky='ns')
SP_weather.grid(row=1, column=0, sticky='nsew')
SP_ambient_light_label.grid(row=2, column=0, sticky='ns')

# Photolithography weather layout
PL_temperature_label.grid(row=0, column=0, sticky='s')
PL_humidity_label.grid(row=1, column=0, sticky='n')

# Spin Coating weather layout
SC_temperature_label.grid(row=0, column=0, sticky='s')
SC_humidity_label.grid(row=1, column=0, sticky='n')

# Sputtering weather layout
SP_temperature_label.grid(row=0, column=0, sticky='s')
SP_humidity_label.grid(row=1, column=0, sticky='n')

# Status frame layout
PL_status_label.grid(row=0, column=0, sticky='ew')
SC_status_label.grid(row=0, column=1, sticky='ew')
SP_status_label.grid(row=0, column=2, sticky='ew')

''' Configure Rows and Columns to expand with window '''
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)
mainframe.rowconfigure(1, weight=1)

toolbar.columnconfigure(0, weight=1)
toolbar.columnconfigure(1, weight=1)
toolbar.columnconfigure(2, weight=1)
toolbar.rowconfigure(0, weight=1)

toolbar_watermarks.columnconfigure(0, weight=1)
toolbar_watermarks.columnconfigure(1, weight=1)
toolbar_watermarks.rowconfigure(0, weight=1)

toolbar_tabs.columnconfigure(0, weight=2)
toolbar_tabs.rowconfigure(0, weight=1)

toolbar_info.columnconfigure(0, weight=1)
toolbar_info.columnconfigure(1, weight=1)
toolbar_info.columnconfigure(2, weight=1)
toolbar_info.columnconfigure(3, weight=1)
toolbar_info.rowconfigure(0, weight=1)

stations.columnconfigure(0, weight=1)
stations.columnconfigure(1, weight=1)
stations.columnconfigure(2, weight=1)
stations.rowconfigure(0, weight=1)
stations.rowconfigure(1, weight=1)

station_PL.columnconfigure(0, weight=1)
station_PL.rowconfigure(0, weight=1)
station_PL.rowconfigure(1, weight=1)
station_PL.rowconfigure(2, weight=1)
station_PL.rowconfigure(3, weight=1)

station_SC.columnconfigure(0, weight=1)
station_SC.rowconfigure(0, weight=1)
station_SC.rowconfigure(1, weight=1)
station_SC.rowconfigure(2, weight=1)
station_SC.rowconfigure(3, weight=1)

station_SP.columnconfigure(0, weight=1)
station_SP.rowconfigure(0, weight=1)
station_SP.rowconfigure(1, weight=1)
station_SP.rowconfigure(2, weight=1)

PL_weather.columnconfigure(0, weight=1)
PL_weather.rowconfigure(0, weight=1)
PL_weather.rowconfigure(1, weight=1)

SC_weather.columnconfigure(0, weight=1)
SC_weather.rowconfigure(0, weight=1)
SC_weather.rowconfigure(1, weight=1)

SP_weather.columnconfigure(0, weight=1)
SP_weather.rowconfigure(0, weight=1)
SP_weather.rowconfigure(1, weight=1)

status.columnconfigure(0, weight=1)
status.columnconfigure(1, weight=1)
status.columnconfigure(2, weight=1)
status.rowconfigure(0, weight=1)

# Set initial status values
STRINGVARS['PL_data']['status'].set('STATUS')
STRINGVARS['SC_data']['status'].set('STATUS')
STRINGVARS['SP_data']['status'].set('STATUS')

# Start the MQTT listener in a separate thread.
listener_thread = threading.Thread(target=listen_to_topic, args=(root, INPUT_TOPIC, STRINGVARS, STATIONS), daemon=True)
listener_thread.start()

# Start the Tkinter main event loop.
root.mainloop()
