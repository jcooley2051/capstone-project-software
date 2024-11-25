from tkinter import *
from tkinter import ttk

root = Tk()
root.title('Hackerfab Monitoring System')
content = ttk.Frame(root)

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


# Test values for StringVars
rmTemp.set('20.6°C')
rmHumidity.set('69%')
time.set('13:37')
date.set('20 April, 2069')
temp_PL.set('37.6°C')
temp_SC.set('64.9°C')
temp_Sp.set('94.3°C')
humidity_PL.set('64%')
humidity_SC.set('42%')
humidity_Sp.set('98%')
partCount.set('at least 4\nParticles')
ambientLight_SC.set('2 LUX')
ambientLight_Sp.set('100 LUX')
vibration_PL.set('wobblin')
vibration_Sp.set('steady as\nshe goes')
status_PL.set('BAD')
status_SC.set('DEGRADED')
status_Sp.set('GOOD')


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

# Columns = 15
# Rows = 16

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

root.mainloop()