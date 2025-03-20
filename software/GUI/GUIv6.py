import tkinter as T
from tkinter import ttk
import json
import subprocess
from datetime import date as D
from time import sleep

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

Sp_SENSORS = ('temperature',
              'humidity',
              'ambient_light')
"""
Create Python Dictionary containing all stations
~~~~~~TEMPLATE~~~~~~
STATIONS = {'St': St_sensors}
"""
STATIONS = {'PL_data': PL_SENSORS,
            'SC_data': SC_SENSORS,
            'SP_data': Sp_SENSORS}

# STATIONS DICTIONARY KEYS TO PACKET READINGS & TKINTER STRINGVARS
# assume consistent with packet (minus time)


def update_vars(root, packet, stringVars, stations):
    '''Create local copy of stations directory'''
    s = stations

    stringVars['TB']['temperature'].set('PLACEHOLDER')
    stringVars['TB']['humidity'].set('PLACEHOLDER')
    stringVars['TB']['time'].set(packet['time'])
    stringVars['TB']['date'].set(D.today())
    
    for station, sensors in s.items():
        for sensor in sensors:
            stringVars[station][sensor].set(packet[station][sensor])
        

    root.update_idletasks()


def listen_to_topic(root, topic, stringVars, stations):
    ''' Function to listen to a specific MQTT topic and update the data dictionary '''
    print(f'Listening to topic: {topic}')  # Debugging statement to check if the function is called

    '''Create local copy of stations directory'''
    s = stations
    
    '''Command arguments to connect to MQTT broker'''
    command = [
        'mosquitto_sub',
        '-h', MQTT_BROKER,  # MQTT host
        '-p', MQTT_PORT,    # MQTT port
        '-t', topic         # MQTT topic
    ]
    
    trying_to_connect = True
    while (trying_to_connect):
        try:
            with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
                for line in proc.stdout:
                    line = line.strip()
                    try:
                        # Update data packet with new sensor readings
                        packet = json.loads(line)
                        
                        # Update StringVars to update GUI
                        update_vars(root, packet, stringVars, stations)
                                
                            
                        # Reset data for next reading                        
                        for station, sensors in s.items():
                            for sensor in sensors:
                                packet[station][sensor] = None 
                        packet['time'] = None
    
                    except ValueError:
                        print(f'Invalid data received on topic "{topic}": {line}')
                        
                trying_to_connect = False
                
        except Exception as e:
            print(f'Error in listening to topic {topic}: {e}')




'''
create tkinter StringVars to store individual values to be displayed
combine string vars into dictionaries to improve readability & pass to methods
'''

"""
Create tkinter StringVars to store individual values to be displayed
Also create dictionaries to hold vars to simplify passing to methods
~~~~~~TEMPLATE~~~~~~
St_reading = T.StringVar()
station_vars = {'reading': St_reading}
"""

# toolbar StringVars
# SHOULD REMAIN THE SAME BETWEEN REVISIONS
TB_temperature = T.StringVar()
TB_humidity = T.StringVar()
time = T.StringVar()
date = T.StringVar()

toolbar_vars = {'temperature': TB_temperature,
                'humidity': TB_humidity,
                'time': time,
                'date': date}





# photolithography StringVars
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

# spin coating StringVars
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

# sputtering StringVars
Sp_temperature = T.StringVar()
Sp_humidity = T.StringVar()
Sp_ambient_light = T.StringVar()
Sp_status = T.StringVar()

sputtering_vars = {'temperature': Sp_temperature,
                   'humidity': Sp_humidity,
                   'ambient_light': Sp_ambient_light,
                   'status': Sp_status}

"""
Create Python Dictionary containing station stringVars
Simplifies passing to methods
~~~~~~TEMPLATE~~~~~~
STRINGVARS = {'St': station_vars}
"""
STRINGVARS = {'TB': toolbar_vars,
              'PL': photolithography_vars,
              'SC': spin_coating_vars,
              'Sp': sputtering_vars}



''' create tkinter frame widgets to organize content widgets '''


# create a main frame in "root" widget to hold organizational sub-frames
mainframe = ttk.Frame(root)


# create toolbar frame in mainframe and sub-frames to hold toolbar content widgets
toolbar = ttk.Frame(mainframe)

toolbar_watermarks = ttk.Frame(toolbar)
toolbar_tabs = ttk.Frame(toolbar)
toolbar_info = ttk.Frame(toolbar)


# create stations frame in mainframe and sub-frames to hold station content widgets
stations = ttk.Frame(mainframe)

station_PL = ttk.Frame(stations)
PL_weather = ttk.Frame(station_PL)
station_SC = ttk.Frame(stations)
SC_weather = ttk.Frame(station_SC)
station_Sp = ttk.Frame(stations)
Sp_weather = ttk.Frame(station_Sp)

status = ttk.Frame(stations)


''' create content widgets to store and display data readings '''

# toolbar content widgets
watermark_HFAB = ttk.Label(toolbar_watermarks, text='Hackerfab')
watermark_OSU = ttk.Label(toolbar_watermarks, text='OSU')
TB_temperature_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['temperature'])
TB_humidity_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['humidity'])
TB_time_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['time'])
TB_date_label = ttk.Label(toolbar_info, textvariable=STRINGVARS['TB']['date'])

# photolithography content widgets

PL_station_label = ttk.Label(station_PL, text='Photolithography')
PL_temperature_label = ttk.Label(PL_weather, textvariable=STRINGVARS['PL']['temperature'])
PL_humidity_label = ttk.Label(PL_weather, textvariable=STRINGVARS['PL']['humidity'])
PL_ambient_light_label = ttk.Label(station_PL, textvariable=STRINGVARS['PL']['ambient_light'])
PL_vibration_label = ttk.Label(station_PL, textvariable=STRINGVARS['PL']['vibration'])
PL_status_label = ttk.Label(status, textvariable=STRINGVARS['PL']['status'])

# spin coating content widgets

SC_station_label = ttk.Label(station_SC, text='Spin Coating')
SC_temperature_label = ttk.Label(SC_weather, textvariable=STRINGVARS['SC']['temperature'])
SC_humidity_label = ttk.Label(SC_weather, textvariable=STRINGVARS['SC']['humidity'])
SC_particle_count_label = ttk.Label(station_SC, textvariable=STRINGVARS['SC']['particle_count'])
SC_vibration_label = ttk.Label(station_SC, textvariable=STRINGVARS['SC']['vibration'])
SC_status_label = ttk.Label(status, textvariable=STRINGVARS['SC']['status'])

# sputtering content widgets

Sp_station_label = ttk.Label(station_Sp, text='Sputtering')
Sp_temperature_label = ttk.Label(Sp_weather, textvariable=STRINGVARS['Sp']['temperature'])
Sp_humidity_label = ttk.Label(Sp_weather, textvariable=STRINGVARS['Sp']['humidity'])
Sp_ambient_light_label = ttk.Label(station_Sp, textvariable=STRINGVARS['Sp']['ambient_light'])
Sp_status_label = ttk.Label(status, textvariable=STRINGVARS['Sp']['status'])



''' tkinter geometry management '''

# place mainframe in root window
mainframe.grid(row=0, column=0, sticky='nsew')



# inside mainframe
toolbar.grid(row=0, column=0, sticky='new')
stations.grid(row=1, column=0, sticky='nsew')



# inside toolbar frame
toolbar_watermarks.grid(row=0, column=0, sticky='nsew')
toolbar_tabs.grid(row=0, column=1, sticky='nsew')
toolbar_info.grid(row=0, column=2, sticky='nsew')

# inside toolbar_watermarks frame
watermark_HFAB.grid(row=0, column=0, sticky='ew')
watermark_OSU.grid(row=0, column=1, sticky='w')

# nothing in toolbar_tabs frame

# inside toolbar_info frame
TB_temperature_label.grid(row=0, column=0, sticky='e')
TB_humidity_label.grid(row=0, column=1, sticky='ew')
TB_time_label.grid(row=0, column=2, sticky='ew')
TB_date_label.grid(row=0, column=3, sticky='ew')



# inside stations frame
station_PL.grid(row=0, column=0, sticky='nsew')
station_SC.grid(row=0, column=1, sticky='nsew')
station_Sp.grid(row=0, column=2, sticky='nsew')
status.grid(row=1, column=0, columnspan=3, sticky='nsew')

# inside station_PL frame
PL_station_label.grid(row=0, column=0, sticky='ns')
PL_weather.grid(row=1, column=0, sticky='nsew')
PL_ambient_light_label.grid(row=2, column=0, sticky='ns')
PL_vibration_label.grid(row=3, column=0, sticky='ns')

# inside station_SC frame
SC_station_label.grid(row=0, column=0, sticky='ns')
SC_weather.grid(row=1, column=0, sticky='nsew')
SC_particle_count_label.grid(row=2, column=0, sticky='ns')
SC_vibration_label.grid(row=3, column=0, sticky='ns')

# inside station_Sp frame
Sp_station_label.grid(row=0, column=0, sticky='ns')
Sp_weather.grid(row=1, column=0, sticky='nsew')
Sp_ambient_light_label.grid(row=2, column=0, sticky='ns')


# inside PL_weather frame
PL_temperature_label.grid(row=0, column=0, sticky='s')
PL_humidity_label.grid(row=1, column=0, sticky='n')

# inside SC_weather frame
SC_temperature_label.grid(row=0, column=0, sticky='s')
SC_humidity_label.grid(row=1, column=0, sticky='n')

# inside Sp_weather frame
Sp_temperature_label.grid(row=0, column=0, sticky='s')
Sp_humidity_label.grid(row=1, column=0, sticky='n')



# inside status frame
PL_status_label.grid(row=0, column=0, sticky='ew')
SC_status_label.grid(row=0, column=1, sticky='ew')
Sp_status_label.grid(row=0, column=2, sticky='ew')









'''Configure Rows and Columns to expand with window'''
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

station_Sp.columnconfigure(0, weight=1)
station_Sp.rowconfigure(0, weight=1)
station_Sp.rowconfigure(1, weight=1)
station_Sp.rowconfigure(2, weight=1)


PL_weather.columnconfigure(0, weight=1)
PL_weather.rowconfigure(0, weight=1)
PL_weather.rowconfigure(1, weight=1)

SC_weather.columnconfigure(0, weight=1)
SC_weather.rowconfigure(0, weight=1)
SC_weather.rowconfigure(1, weight=1)

Sp_weather.columnconfigure(0, weight=1)
Sp_weather.rowconfigure(0, weight=1)
Sp_weather.rowconfigure(1, weight=1)

status.columnconfigure(0, weight=1)
status.columnconfigure(1, weight=1)
status.columnconfigure(2, weight=1)
status.rowconfigure(0, weight=1)



STRINGVARS['PL']['status'].set('STATUS')
STRINGVARS['SC']['status'].set('STATUS')
STRINGVARS['Sp']['status'].set('STATUS')



while True:
    sleep(1)
    listen_to_topic(root, INPUT_TOPIC, STRINGVARS, STATIONS)
