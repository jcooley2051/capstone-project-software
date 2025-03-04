import tkinter as T
from tkinter import ttk
import json
import subprocess
from datetime import datetime
from time import sleep

# create "root" widget
root = T.Tk()
root.title('Hackerfab Monitoring System')


# MQTT configuration
MQTT_BROKER = 'localhost'
MQTT_PORT = '1337'
INPUT_TOPIC = 'analysis/results'




def update_vars(root, reading, stringVars):
    
    stringVars['TB']['temp'].set('PLACEHOLDER')
    stringVars['TB']['humidity'].set('PLACEHOLDER')
    stringVars['TB']['time'].set('PLACEHOLDER')
    stringVars['TB']['date'].set('PLACEHOLDER')
    
    stringVars['PL']['temp'].set(reading['temperature'])
    stringVars['PL']['humidity'].set(reading['humidity'])
    stringVars['PL']['light'].set(reading['light'])
    stringVars['PL']['vibration'].set(reading['vibration'])
    stringVars['PL']['status'].set('PLACEHOLDER')

    stringVars['SC']['temp'].set(reading['temperature'])
    stringVars['SC']['humidity'].set(reading['humidity'])
    stringVars['SC']['particle'].set(reading['particle'])
    stringVars['SC']['vibration'].set(reading['vibration'])
    stringVars['SC']['status'].set('PLACEHOLDER')

    stringVars['Sp']['temp'].set(reading['temperature'])
    stringVars['Sp']['humidity'].set(reading['humidity'])
    stringVars['Sp']['light'].set(reading['light'])
    stringVars['Sp']['status'].set('PLACEHOLDER')

    

    root.update_idletasks()


def listen_to_topic(topic):
    ''' Function to listen to a specific MQTT topic and update the data dictionary '''
    print(f'Listening to topic: {topic}')  # Debugging statement to check if the function is called
    
    command = [
        'mosquitto_sub',
        '-h', MQTT_BROKER,
        '-p', MQTT_PORT,
        '-t', topic
    ]
    
    trying_to_connect = True
    while (trying_to_connect):
        try:
            with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
                for line in proc.stdout:
                    line = line.strip()
                    try:
                        # Update the corresponding key in the dictionary
                        data = json.loads(line)
                        
                        

                        
                        
                        display_data = True
                             
                        
                        if display_data:
                            # Prepare the data point to be displayed
                            dPoint = {
                                    'temperature': data['temperature'],
                                    'humidity': data['humidity'],
                                    'light': data['light'],
                                    'particle': data['particle'],
                                    'time': data['time']
                                    }
                            
                            
                            
                            
                            
                            # Update StringVars to update GUI
                            update_vars(root, dPoint, stringVars)
                                
                                
                            # Reset data for next reading                            
                            data['temperature'] = None
                            data['humidity'] = None
                            data['light'] = None
                            data['particle'] = None
                            data['time'] = None

    
                    except ValueError:
                        print(f'Invalid data received on topic "{topic}": {line}')
                        
                trying_to_connect = False
                
        except Exception as e:
            print(f'Error in listening to topic {topic}: {e}')




'''
create tkinter StringVars to store individual values to be displayed
combine string vars into dictionaries to improve readability
'''

# toolbar StringVars
room_temperature = T.StringVar()
room_humidity = T.StringVar()
time = T.StringVar()
date = T.StringVar()

toolbar_vars = {'temp': room_temperature,
                'humidity': room_humidity,
                'time': time,
                'date': date}

# photolithography StringVars
PL_temperature = T.StringVar()
PL_humidity = T.StringVar()
PL_ambient_light = T.StringVar()
PL_vibration = T.StringVar()
PL_status = T.StringVar()

photolithography_vars = {'temp': PL_temperature,
                         'humidity': PL_humidity,
                         'light': PL_ambient_light,
                         'vibration': PL_vibration,
                         'status': PL_status}

# spin coating StringVars
SC_temperature = T.StringVar()
SC_humidity = T.StringVar()
SC_particle_count = T.StringVar()
SC_vibration = T.StringVar()
SC_status = T.StringVar()

spin_coating_vars = {'temp': SC_temperature,
                     'humidity': SC_humidity,
                     'particle': SC_particle_count,
                     'vibration': SC_vibration,
                     'status': SC_status}

# sputtering StringVars
Sp_temperature = T.StringVar()
Sp_humidity = T.StringVar()
Sp_ambient_light = T.StringVar()
Sp_status = T.StringVar()

sputtering_vars = {'temp': Sp_temperature,
                   'humidity': Sp_humidity,
                   'light': Sp_ambient_light,
                   'status': Sp_status}


# combine string vars into single dictionary to simplify passing to methods
stringVars = {'TB': toolbar_vars,
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



''' create content widgets to store and display data readings '''

# toolbar content widgets
watermark_HFAB = ttk.Label(toolbar_watermarks, text='Hackerfab')
watermark_OSU = ttk.Label(toolbar_watermarks, text='OSU')
room_info_temp = ttk.Label(toolbar_info, textvariable=stringVars['TB']['temp'])
room_info_humidity = ttk.Label(toolbar_info, textvariable=stringVars['TB']['humidity'])
room_info_time = ttk.Label(toolbar_info, textvariable=stringVars['TB']['time'])
room_info_date = ttk.Label(toolbar_info, textvariable=stringVars['TB']['date'])

# photolithography content widgets

PL_station_label = ttk.Label(station_PL, text='Photolithography')
PL_temperature_label = ttk.Label(PL_weather, textvariable=stringVars['PL']['temp'])
PL_humidity_label = ttk.Label(PL_weather, textvariable=stringVars['PL']['humidity'])
PL_ambient_light_label = ttk.Label(station_PL, textvariable=stringVars['PL']['light'])
PL_vibration_label = ttk.Label(station_PL, textvariable=stringVars['PL']['vibration'])
PL_status_label = ttk.Label(station_PL, textvariable=stringVars['PL']['status'])

# spin coating content widgets

SC_station_label = ttk.Label(station_SC, text='Spin Coating')
SC_temperature_label = ttk.Label(SC_weather, textvariable=stringVars['SC']['temp'])
SC_humidity_label = ttk.Label(SC_weather, textvariable=stringVars['SC']['humidity'])
SC_particle_count_label = ttk.Label(station_SC, textvariable=stringVars['SC']['particle'])
SC_vibration_label = ttk.Label(station_SC, textvariable=stringVars['SC']['vibration'])
SC_status_label = ttk.Label(station_SC, textvariable=stringVars['SC']['status'])

# sputtering content widgets

Sp_station_label = ttk.Label(station_Sp, text='Sputtering')
Sp_temperature_label = ttk.Label(Sp_weather, textvariable=stringVars['Sp']['temp'])
Sp_humidity_label = ttk.Label(Sp_weather, textvariable=stringVars['Sp']['humidity'])
Sp_ambient_light_label = ttk.Label(station_Sp, textvariable=stringVars['Sp']['light'])
Sp_status_label = ttk.Label(station_Sp, textvariable=stringVars['Sp']['status'])



''' tkinter geometry management '''

# place mainframe in root window
mainframe.grid(row=0, column=0, rowspan=17, columnspan=30, sticky='nsew')


# palce toolbar frame in mainframe with nested sub-frames
toolbar.grid(row=0, column=0, columnspan=30, sticky='nsew')
toolbar_watermarks.grid(column=0, columnspan=6, sticky='nsew')
toolbar_tabs.grid(column=6, columnspan=14, sticky='nsew')
toolbar_info.grid(column=20, columnspan=10, sticky='nsew')

# place toolbar content widgets to display on GUI
# watermark content widgets
watermark_HFAB.grid(column=0, columnspan=4, sticky='nsew')
watermark_OSU.grid(column=4, columnspan=2, sticky='nsew')

# info content widgets
room_info_temp.grid(column=0, columnspan=2, sticky='nsew')
room_info_humidity.grid(column=2, columnspan=2, sticky='nsew')
room_info_time.grid(column=4, columnspan=2, sticky='nsew')
room_info_date.grid(column=6, columnspan=4, sticky='nsew')


# place stations frame in mainframe with nested sub-frames
stations.grid(row=1, column=0, rowspan=16, columnspan=30, sticky='nsew')
station_PL.grid(column=0, columnspan=10, sticky='nsew')
PL_weather.grid(row=3, rowspan=3, sticky='nsew')
station_SC.grid(column=10, columnspan=10, sticky='nsew')
SC_weather.grid(row=3, rowspan=3, sticky='nsew')
station_Sp.grid(column=20, columnspan=10, sticky='nsew')
Sp_weather.grid(row=3, rowspan=3, sticky='nsew')

# place station content widgets to display on GUI
# photolithography content widgets
PL_station_label.grid(row=0, rowspan=3, sticky='nsew')
PL_temperature_label.grid(row=0, sticky='s')
PL_humidity_label.grid(row=1, sticky='n')
PL_ambient_light_label.grid(row=6, rowspan=3, sticky='nsew')
PL_vibration_label.grid(row=9, rowspan=5, sticky='nsew')
PL_status_label.grid(row=14, rowspan=2, sticky='nsew')

# spin coating content widgets
SC_station_label.grid(row=0, rowspan=3, sticky='nsew')
SC_temperature_label.grid(row=0, sticky='s')
SC_humidity_label.grid(row=1, sticky='n')
SC_particle_count_label.grid(row=6, rowspan=3, sticky='nsew')
SC_vibration_label.grid(row=9, rowspan=5, sticky='nsew')
SC_status_label.grid(row=14, rowspan=2, sticky='nsew')

# sputtering content widgets
Sp_station_label.grid(row=0, rowspan=3, sticky='nsew')
Sp_temperature_label.grid(row=0, sticky='s')
Sp_humidity_label.grid(row=1, sticky='n')
Sp_ambient_light_label.grid(row=6, rowspan=3, sticky='nsew')
Sp_status_label.grid(row=14, rowspan=2, sticky='nsew')



# Configure Rows and Columns to expand with window
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

for col in range(0, 29):
    mainframe.columnconfigure(col, weight=1)
    
for row in range(0, 16):
    mainframe.rowconfigure(row, weight=1)



while True:
    sleep(1)
    listen_to_topic(INPUT_TOPIC)
