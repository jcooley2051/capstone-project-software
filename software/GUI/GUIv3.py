from tkinter import *
from tkinter import ttk
import json
import subprocess
from datetime import datetime
from threading import Thread, Lock

# Create "root" widget
root = Tk()
root.title('Hackerfab Monitoring System')
# Create a content frame to hold all the widgets
content = ttk.Frame(root)

# Setup Variables for GUI
# Toolbar vars
rmTemp = StringVar()
rmHumidity = StringVar()
time = StringVar()
date = StringVar()
# Station Temperature Vars
temp_PL = StringVar()
temp_SC = StringVar()
temp_Sp = StringVar()
# Station Humidity Vars
humidity_PL = StringVar()
humidity_SC = StringVar()
humidity_Sp = StringVar()
# Particle Count Var
partCount = StringVar()
# Station Ambient Light Vars
ambientLight_SC = StringVar()
ambientLight_Sp = StringVar()
# Station Vibration Vars
vibration_PL = StringVar()
vibration_Sp = StringVar()
# Station Status Vars
status_PL = StringVar()
status_SC = StringVar()
status_Sp = StringVar()

# Combine string vars into single dictionary to simplify passing to methods
toolbar_vars = {'temp': rmTemp, 'humidity': rmHumidity, 'time': time, 'date': date}
temp_vars = {'PL': temp_PL, 'SC': temp_SC, 'SP': temp_Sp}
humidity_vars = {'PL': humidity_PL, 'SC': humidity_SC, 'SP': humidity_Sp}
ambientLight_vars = {'SC': ambientLight_SC, 'SP': ambientLight_Sp}
vibration_vars = {'PL': vibration_PL, 'SP': vibration_Sp}
status_vars = {'PL': status_PL, 'SC': status_SC, 'SP': status_Sp}

stringVars = {'toolbar': toolbar_vars, 'temp': temp_vars, 'humidity': humidity_vars, 
              'partCount': partCount, 'ambientLight': ambientLight_vars, 
              'vibration': vibration_vars, 'status': status_vars}



# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1337
INPUT_TOPIC = 'analysis/results'

# Dictionary to store temperature and humidity data
data = {"temperature": None, "humidity": None, "time": None}

# Lock to ensure thread-safe updates to the data dictionary
data_lock = Lock()

def listen_to_topic(topic, key):
    """Function to listen to a specific MQTT topic and update the data dictionary."""
    print(f"Listening to topic: {topic}")  # Debugging statement to check if the function is called
    
    command = [
        "mosquitto_sub",
        "-h", MQTT_BROKER,
        "-p", str(MQTT_PORT),
        "-t", topic
    ]

    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                line = line.strip()
                
                try:
                    # Update the corresponding key in the dictionary
                    with data_lock:  # Use the lock to ensure thread safety
                        data = json.loads(line)

                    # Check if both temperature and humidity are updated
                    with data_lock:
                        if data["temperature"] is not None and data["humidity"] is not None:
                            # Print the temperature in Celsius and humidity
                            # print(f"Temperature: {data['temp']}°C, Humidity: {data['humidity']}%, Time: {data['time'].strftime('%Y-%m-%d %H:%M:%S')}")
                            # Prepare the data point to be displayed
                            dPoint = {
                                "temperature": data["temperature"],
                                "humidity": data["humidity"],
                                "time": data["time"]
                            }
                            # Display info from data point in GUI
                            # Add main code to a method
                            update_Vars(dPoint, stringVars)
                            update_GUI()
                            
                            
                            # Reset data for next reading
                            data["temperature"], data["humidity"] = None, None

                except ValueError:
                    print(f"Invalid data received on topic '{topic}': {line}")

    except Exception as e:
        print(f"Error in listening to topic {topic}: {e}")


def update_Vars(dPoint, stringVars):
    stringVars['toolbar']['temp'].set(dPoint['temperature'])
    stringVars['toolbar']['humidity'].set(dPoint['humidity'])
    stringVars['toolbar']['time'].set(datetime.now().isoformat())
    stringVars['toolbar']['date'].set(datetime.now().isoformat())

    stringVars['temp']['PL'].set(dPoint['temperature'])
    stringVars['temp']['SP'].set(dPoint['temperature'])
    stringVars['temp']['SC'].set(dPoint['temperature'])
    
    stringVars['humidity']['PL'].set(dPoint['humidity'])    
    stringVars['humidity']['SC'].set(dPoint['humidity'])
    stringVars['humidity']['SP'].set(dPoint['humidity'])
    
    stringVars['partCount'].set('PLACEHOLDER')
    
    stringVars['ambientLight']['SC'].set('PLACEHOLDER')
    stringVars['ambientLight']['SP'].set('PLACEHOLDER')
    
    stringVars['vibration']['PL'].set('PLACEHOLDER')
    stringVars['vibration']['SP'].set('PLACEHOLDER')
    
    stringVars['status']['PL'].set('PLACEHOLDER')
    stringVars['status']['SC'].set('PLACEHOLDER')
    stringVars['status']['SP'].set('PLACEHOLDER')


def update_GUI():
    # Update content widgets
    # Toolbar Widgets
    toolbar_HFAB = ttk.Label(content, text='Hackerfab', relief='solid')
    toolbar_OSU = ttk.Label(content, text='OSU', relief='solid')
    toolbar_Temp = ttk.Label(content, textvariable=rmTemp, relief='solid')
    toolbar_Humidity = ttk.Label(content, textvariable=rmHumidity, relief='solid')
    toolbar_Time = ttk.Label(content, textvariable=time, relief='solid')
    toolbar_Date = ttk.Label(content, textvariable=date, relief='solid')

    # Photolithography Station Widgets
    station_PL_Label = ttk.Label(content, text='Photolithography', font='TkHeadingFont')
    station_PL_Temperature = ttk.Label(content, textvariable=temp_PL)
    station_PL_Humidity = ttk.Label(content, textvariable=humidity_PL)
    station_PL_PartCount = ttk.Label(content, textvariable=partCount)
    station_PL_Vibration = ttk.Label(content, textvariable=vibration_PL)
    station_PL_Status = ttk.Label(content, textvariable=status_PL)

    # Spin Coating Station Widgets
    station_SC_Label = ttk.Label(content, text='Spin Coating', font='TkHeadingFont')
    station_SC_Temperature = ttk.Label(content, textvariable=temp_SC)
    station_SC_Humidity = ttk.Label(content, textvariable=humidity_SC)
    station_SC_Ambient_Light = ttk.Label(content, textvariable=ambientLight_SC)
    station_SC_Status = ttk.Label(content, textvariable=status_SC)

    # Sputtering Station Widgets
    station_Sp_Label = ttk.Label(content, text='Sputtering', font='TkHeadingFont')
    station_Sp_Temperature = ttk.Label(content, textvariable=temp_Sp)
    station_Sp_Humidity = ttk.Label(content, textvariable=humidity_Sp)
    station_Sp_Ambient_Light = ttk.Label(content, textvariable=ambientLight_Sp)
    station_Sp_Vibration = ttk.Label(content, textvariable=vibration_Sp)
    station_Sp_Status = ttk.Label(content, textvariable=status_Sp)
    
    
    # GUI Grometry Manager
    content.grid(column=0, row=0, sticky='nsew')

    toolbar_HFAB.grid(column=0, columnspan=2, row=0, sticky='new')
    toolbar_OSU.grid(column=2, row=0, sticky='nw')
    toolbar_Temp.grid(column=10, row=0, sticky='ne')
    toolbar_Humidity.grid(column=11, row=0, sticky='new')
    toolbar_Time.grid(column=12, row=0, sticky='new')
    toolbar_Date.grid(column=13, columnspan=2, row=0, sticky='new')

    station_PL_Label.grid(column=0, columnspan=5, row=1, rowspan=3, sticky='ns')
    station_PL_Temperature.grid(column=0, columnspan=5, row=4, rowspan=2, sticky='s')
    station_PL_Humidity.grid(column=0, columnspan=5, row=6, rowspan=2, sticky='n')
    station_PL_PartCount.grid(column=0, columnspan=5, row=8, rowspan=2, sticky='ns')
    station_PL_Vibration.grid(column=0, columnspan=5, row=10, rowspan=4, sticky='ns')
    station_PL_Status.grid(column=0, columnspan=5, row=14, rowspan=2, sticky='ns')

    station_SC_Label.grid(column=5, columnspan=5, row=1, rowspan=3, sticky='ns')
    station_SC_Temperature.grid(column=5, columnspan=5, row=4, rowspan=2, sticky='s')
    station_SC_Humidity.grid(column=5, columnspan=5, row=6, rowspan=2, sticky='n')
    station_SC_Ambient_Light.grid(column=5, columnspan=5, row=8, rowspan=2, sticky='ns')
    station_SC_Status.grid(column=5, columnspan=5, row=14, rowspan=2, sticky='ns')

    station_Sp_Label.grid(column=10, columnspan=5, row=1, rowspan=3, sticky='ns')
    station_Sp_Temperature.grid(column=10, columnspan=5, row=4, rowspan=2, sticky='s')
    station_Sp_Humidity.grid(column=10, columnspan=5, row=6, rowspan=2, sticky='n')
    station_Sp_Ambient_Light.grid(column=10, columnspan=5, row=8, rowspan=2, sticky='ns')
    station_Sp_Vibration.grid(column=10, columnspan=5, row=10, rowspan=4, sticky='ns')
    station_Sp_Status.grid(column=10, columnspan=5, row=14, rowspan=2, sticky='ns')

    # Configure Rows and Columns to expand with window
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)
    content.columnconfigure(2, weight=1)
    content.columnconfigure(3, weight=1)
    content.columnconfigure(4, weight=1)
    content.columnconfigure(5, weight=1)
    content.columnconfigure(6, weight=1)
    content.columnconfigure(7, weight=1)
    content.columnconfigure(8, weight=1)
    content.columnconfigure(9, weight=1)
    content.columnconfigure(10, weight=1)
    content.columnconfigure(11, weight=1)
    content.columnconfigure(12, weight=1)
    content.columnconfigure(13, weight=1)
    content.columnconfigure(14, weight=1)
    content.rowconfigure(0, weight=1)
    content.rowconfigure(1, weight=1)
    content.rowconfigure(2, weight=1)
    content.rowconfigure(3, weight=1)
    content.rowconfigure(4, weight=1)
    content.rowconfigure(5, weight=1)
    content.rowconfigure(6, weight=1)
    content.rowconfigure(7, weight=1)
    content.rowconfigure(8, weight=1)
    content.rowconfigure(9, weight=1)
    content.rowconfigure(10, weight=1)
    content.rowconfigure(11, weight=1)
    content.rowconfigure(12, weight=1)
    content.rowconfigure(13, weight=1)
    content.rowconfigure(14, weight=1)
    content.rowconfigure(15, weight=1)




'''
dPoint = {'temperature': '69°', 'humidity': '82%'}
update_Vars(dPoint, stringVars)
update_GUI()
'''

# Create threads to listen to each node
node1_thread = Thread(target=listen_to_topic, args=(INPUT_TOPIC, "node1"))

# Start both threads
node1_thread.start()

# Wait for both threads to finish
node1_thread.join()


root.mainloop()


