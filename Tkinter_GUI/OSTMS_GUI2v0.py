"""
Title: On-Instrument Slide Temperature Measurement System GUI
Version: 2.0
Author: Nestor Garcia
Date: 08 Mar 24
Partnership: Developed in partnership between University of Arizona Senior Design and Roche.

Description:
This application is designed to facilitate real-time temperature monitoring and visualization for laboratory slides. 
It integrates hardware control, data acquisition, and graphical display within a user-friendly interface. 
Key features include serial communication for temperature data collection, dynamic plotting of temperature distributions, 
and the ability to scan for and connect to available serial ports. The system aims to enhance laboratory experiments and 
research by providing accurate and immediate temperature readings.

Features:
- Real-time temperature monitoring for up to six different points.
- Graphical representation of temperature distribution using matplotlib.
- Serial port communication with automatic detection of available ports.
- Customizable baud rate selection for serial communication.
- Log generation for temperature data, including timestamp and values.
- GUI developed using Tkinter for ease of use and accessibility.

Requirements:
- Python 3.x
- External Libraries: Tkinter, NumPy, Matplotlib, SciPy, PySerial
- Compatible with Windows, macOS, and Linux operating systems.

Usage:
To run the application, ensure all dependencies are installed and execute the main script through a Python interpreter. 
The interface allows users to scan for serial ports, connect to a selected port, and begin temperature data acquisition 
and visualization.

Major Updates in version 2.0:
- Database Integration for Calibration Data
- Calibration Functionality
- Imporived Serial Communication Handling:
- Thermistor Sensor and Assembly Classes
- User Interface Improvements
- Refined Data Processing (calibration)
- Logging and Data Handling Enhancements
- Structural and Functional Enhancements
- Management ans storage of multiple Thermistor Sensor Assemblies
- Improved GUI Aesthetics and Layout

Acknowledgments:
This project was made possible through the collaborative efforts of Roche and the University of Arizona. 
Special thanks to all team members and contributors for their dedication and support throughout the development process.

License:
[Specify the license under which this software is released, e.g., MIT, GPL, etc.]

Contact Information:
For further information, questions, or feedback, please contact:
Nestor Garcia
Nestor212@arizona.edu.
"""


import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.interpolate import Rbf
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
import threading
from datetime import datetime
import csv
import os
# Placeholder for the serial port import
import serial
# Placeholder for listing serial ports
from serial.tools import list_ports
import sqlite3


ICON_PATH = os.path.join(os.path.dirname(__file__), "ENGR498_Logo.png")

class GUI:
    def __init__(self, title):
        self.isStarted = False
        now = datetime.now()
        self.start_dt = now.strftime("%Y_%m_%d_%H:%M")
        self.timer = 0
        
        self.window = tk.Tk()
        self.window.title(title)
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):  # Check if the icon file exists
                self.window.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
        except Exception as e:
            print(f"Error setting icon: {e}")  # Log the error
        
        self.portNamesList = []
        self.tsaList = [1, 2, 3, 4, 5, 6]
        
        self.guiUpdateInterval = 1000
        self.tsaSelect = 1
        self.serialPortManager = SerialPortManager()
        self.get_available_serial_ports()

        self.create_db_and_table()
        self.create_widgets()
        
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.points = np.array([(1.125, 0.75), (2.625, 0.75), (1.5750, 0.5), (2.125, 0.5), (1.125, 0.25), (2.625, 0.25)])
        #self.points = np.array([(0.5, 0.75), (2.5, 0.75), (1.15, 0.5), (1.85, 0.5), (0.5, 0.25), (2.5, 0.25)])
        self.temperatures = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        # Calibration data       [rawLow, refLow, rawHigh, refHigh]
        self.calibration = np.array([39.5, 40.0, 63.5, 65.0])
        
        self.updateTemperaturePlot(True)
        
        # Bind the close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Top frame for controls
        self.topFrame = tk.Frame(self.window, bg="#303030")
        self.topFrame.pack(side=tk.TOP, fill=tk.X)

        # Scan button
        self.scanButton = tk.Button(self.topFrame, text="Scan", command=self.scan_ports)
        self.scanButton.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Ports Label
        self.scanButton = tk.Label(self.topFrame, text="Ports")
        self.scanButton.pack(side=tk.LEFT, padx=5, pady=20)
        
        # Serial port selection dropdown
        self.isAnyPortAvailable = False
        self.selectedPort = tk.StringVar()
        # Set default value of selectedPort
        if self.isAnyPortAvailable == False:
            self.portNamesList = ["No ports available"]
        self.selectedPort.set(self.portNamesList[0])
        self.portVar = tk.StringVar(self.window)
        self.portDropdown =ttk.Combobox(self.topFrame, textvariable=self.selectedPort, values=self.portNamesList, state='disabled')
        # self.portDropdown = ttk.Combobox(self.topFrame, textvariable=self.portVar, values=["COM3", "COM4"])  # Example values
        self.portDropdown.pack(side=tk.LEFT, padx=5, pady=20)
        # Assuming self.portDropdown is your combobox
        self.portDropdown.bind('<<ComboboxSelected>>', self.on_combobox_select)
        
        # TSA Label
        self.tsaLabel = tk.Label(self.topFrame, text="TSA Select")
        self.tsaLabel.pack(side=tk.LEFT, padx=5, pady=20)
        
        # TSA Select dropdown
        self.tsaVar = tk.StringVar(self.window)
        self.tsaDropdown = ttk.Combobox(self.topFrame, textvariable=self.tsaVar, values=self.tsaList, state='disabled')  # Example values
        self.tsaDropdown.set(self.tsaList[0])
        self.tsaDropdown.pack(side=tk.LEFT, padx=5, pady=20)
        self.tsaDropdown.bind('<<ComboboxSelected>>', self.on_combobox_select)
        
        self.calibrateButton = tk.Button(self.topFrame, text="Calibrate", command=self.open_calibration_window)
        self.calibrateButton.pack(side=tk.LEFT, padx=(5, 5), pady=20)
        
        self.calOnVar = tk.BooleanVar()
        self.calOnVar.set(True)  # Default to unchecked
        self.calOnCheckbox = tk.Checkbutton(self.topFrame, text="Cal On", variable=self.calOnVar, onvalue=True, offvalue=False, bg="#303030", fg="white")
        self.calOnCheckbox.pack(side=tk.LEFT, padx=(5, 5), pady=20)   
        
        # Define a BooleanVar to track the checkbox state
        self.logDataVar = tk.BooleanVar()
        self.logDataVar.set(False)  # Default to unchecked
        # Create the checkbox and place it
        self.logDataCheckbox = tk.Checkbutton(self.topFrame, text="Log Data", variable=self.logDataVar, onvalue=True, offvalue=False, bg="#303030", fg="white")
        self.logDataCheckbox.pack(side=tk.LEFT, padx=(5, 5), pady=20)
        self.logDataCheckbox.config(state="disabled")
        
        self.refOnVar = tk.BooleanVar()
        self.refOnVar.set(False)  # Default to unchecked
        self.refOnCheckbox = tk.Checkbutton(self.topFrame, text="Ref On", variable=self.refOnVar, onvalue=True, offvalue=False, bg="#303030", fg="white", command=self.refStatus)
        self.refOnCheckbox.pack(side=tk.LEFT, padx=(5, 5), pady=20)   
        
        # LED indicator as a canvas, updated to draw a circle
        self.ledIndicator = tk.Canvas(self.topFrame, width=20, height=20, bg="#303030", highlightthickness=0)  # Background as white or any neutral color
        self.ledCircle = self.ledIndicator.create_oval(2, 2, 18, 18, fill="red")  # Start as red (disconnected)
        self.ledIndicator.pack(side=tk.LEFT, padx=(50, 0), pady=20)
        
        # Connect button
        self.connectButton = tk.Button(self.topFrame, text="Connect", command=self.connect, state='disabled')
        self.connectButton.pack(side=tk.LEFT, padx=(10, 40), pady=20)
              
        self.temp = [tk.Label()] * 6
        self.thermistor = [tk.Label()] * 6
        self.temperatureDataBox = tk.LabelFrame(self.window, text="Temperatures",labelanchor ='n', font=("Helvetica", 24, 'bold'), fg = "#000000", bd = 0, bg="#ffffff", height = 200, width=self.window.winfo_width())
        self.temperatureDataBox.pack(side=tk.TOP, fill = tk.X)        
        
        self.thermistor[0] = tk.Label(self.temperatureDataBox, text="T1", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[0].place(x = 250, y = 5)
        self.temp[0] = tk.Label(self.temperatureDataBox, text="0.00°C", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.temp[0].place(x = 250-10, y = 10+20)
        
        self.thermistor[1] = tk.Label(self.temperatureDataBox, text="T2", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[1].place(x = 800, y = 5)
        self.temp[1] = tk.Label(self.temperatureDataBox, text="00.0°C", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.temp[1].place(x = 800-10, y = 10+20)
        
        self.thermistor[2] = tk.Label(self.temperatureDataBox, text="T3", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[2].place(x = 430, y = 50)
        self.temp[2] = tk.Label(self.temperatureDataBox, text="0.00°C", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.temp[2].place(x = 430-10, y = 60+20)     
        
        self.thermistor[3] = tk.Label(self.temperatureDataBox, text="T4", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[3].place(x = 600, y = 50)
        self.temp[3] = tk.Label(self.temperatureDataBox, text="0.00°C", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.temp[3].place(x = 600-10, y = 60+20)
        
        self.thermistor[4] = tk.Label(self.temperatureDataBox, text="T5", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[4].place(x = 250, y = 100)
        self.temp[4] = tk.Label(self.temperatureDataBox, text="0.00°C", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.temp[4].place(x = 250-10, y = 110+20)
        
        self.thermistor[5] = tk.Label(self.temperatureDataBox, text="T6", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[5].place(x = 800, y = 100)
        self.temp[5] = tk.Label(self.temperatureDataBox, text="0.00°C", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.temp[5].place(x = 800-10, y = 110+20)
        
        self.refLabel = tk.Label(self.temperatureDataBox, text="Ref:  ", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.refLabel.place(x = 950, y = 60)
        self.refTempLabel = tk.Label(self.temperatureDataBox, text="Off", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.refTempLabel.place(x = 950+50, y = 60)
        
        self.datetimeLabel = tk.Label(self.temperatureDataBox, text="Datetime: ", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg = "#000000")
        self.datetimeLabel.place(x = 950, y = 0)
        self.datetimeData = tk.Label(self.temperatureDataBox, text="0.00", font=("Helvetica", 20), bg="#ffffff", fg = "#000000")
        self.datetimeData.place(x = 950+100, y = 0)
        
        # ScrolledText for logging
        self.log = scrolledtext.ScrolledText(self.window, height=10)
        self.log.pack(side=tk.BOTTOM, fill=tk.X)
        
    def on_combobox_select(self, event=None):
        """
        Event handler called when an item is selected in the combobox.
        It changes the focus to the main window to prevent the combobox from trapping the focus.
        """
        self.window.focus_set()
        
    def scan_ports(self):
        threading.Thread(target=self._scan_ports_thread, daemon=True).start()

    def _scan_ports_thread(self):
        self.log.insert(tk.END, "Scanning ports...\n")
        portNamesList = self.get_available_serial_ports()

        if not portNamesList:
            portNamesList = ["No ports available"]
            self.portDropdown.configure(state="disabled")
            self.tsaDropdown.configure(state="disabled")
            self.connectButton.configure(state="disabled")
        else:
            self.isAnyPortAvailable = True
            self.portDropdown.configure(state="normal")
            self.tsaDropdown.configure(state="normal")
            if self.isStarted:
                self.connectButton.configure(state="normal")
            else:
                self.connectButton.configure(state="normal")

        self.window.after(100, lambda: self.update_option_menu(portNamesList))
                  
    def update_option_menu(self, portNames):
        # Remove old items
        self.portDropdown.delete(0, "end")
        # Set default value of selectedPort
        self.portDropdown['values'] = portNames
        self.selectedPort.set(portNames[0])
        
    # def set_tsa(self, TSA): 
    #     data = self.get_calibration_data(TSA) 
    #     self.calibration[0] = data[1]
    #     self.calibration[1] = data[2]
    #     self.calibration[2] = data[3]
    #     self.calibration[3] = data[4]
        
    def refStatus(self):
        print("sending ref command")
        if(self.refOnVar.get()):
            self.serialPortManager.send_serial("REF ON")
        else:
            self.serialPortManager.send_serial("REF OFF")
            
    def connect(self):
        if not self.isStarted:
            self.log.insert(tk.END, "Connecting...\n")
            self.isStarted = True
            self.logDataCheckbox.config(state="normal")
            self.calibrateButton.config(state="disable")
            self.connectButton.configure(text="Disconnect")
            self.serialPortName = self.selectedPort.get()
            self.tsaSelect = int(self.tsaVar.get())
            try:
                self.serialPortManager.stop()  # Ensure previous connection is properly closed
                self.serialPortManager.set_name(self.serialPortName)
                self.TSA = self.load_thermistor_sensor_assembly(self.tsaSelect)
                
                self.serialPortManager.start()
                self.log.insert(tk.END, "Connected to: " + self.serialPortName + "\n")
                self.window.after(100, lambda: self.ledIndicator.itemconfig(self.ledCircle, fill="green"))  # Change LED to green
                self.recursive_update_textbox(True)
            except Exception as e:
                self.log.insert(tk.END, f"Failed to connect: {e}\n")
                self.isStarted = False
                self.window.after(100, lambda: self.ledIndicator.itemconfig(self.ledCircle, fill="red"))  # Ensure LED is red on failure
                self.connectButton.configure(text="Connect")
        else:
            self.isStarted = False
            self.logDataCheckbox.config(state="disabled")
            self.calibrateButton.config(state="normal")
            self.connectButton.configure(text="Connect")
            self.serialPortManager.stop()
            self.log.insert(tk.END, "Disconnected.\n")
            self.ledIndicator.itemconfig(self.ledCircle, fill="red")  # Change LED to red

    def updateTemperatures(self):
        # print(self.buffer)
        thermtokens1 = self.buffer.rstrip().split(" | ")
        rawLow = self.calibration[0]
        refLow = self.calibration[1]
        rawHigh = self.calibration[2]
        refHigh = self.calibration[3]
        rawRange = rawHigh - rawLow
        refRange = refHigh - refLow

        if thermtokens1[0] == 'Data':
            del thermtokens1[0]
            for i in thermtokens1:
                thermTokens = i.split(" ")
                
                if self.calOnVar.get():
                    temp = (((float(thermTokens[1]) - rawLow) * refRange)/rawRange) + refLow; 
                else:
                    temp = float(thermTokens[1])
                temp_str = "{:.2f}".format(temp)
            
                if thermTokens[0] == 'T1':
                    self.temp[0].configure(text = temp_str + "°C")
                    self.temperatures[0] = temp
                elif thermTokens[0] == 'T2':
                    self.temp[1].configure(text = temp_str + "°C")
                    self.temperatures[1] = temp
                elif thermTokens[0] == 'T3':
                    self.temp[2].configure(text = temp_str + "°C")
                    self.temperatures[2] = temp
                elif thermTokens[0] == 'T4':
                    self.temp[3].configure(text = temp_str + "°C")
                    self.temperatures[3] = temp
                elif thermTokens[0] == 'T5':
                    self.temp[4].configure(text = temp_str + "°C") 
                    self.temperatures[4] = temp     
                elif thermTokens[0] == 'T6':
                    self.temp[5].configure(text = temp_str + "°C")    
                    self.temperatures[5] = temp
                if self.refOnVar.get():
                    if thermTokens[0] == 'Ref':
                        self.refTempLabel.configure(text = temp_str + "°C")
                else:
                    self.refTempLabel.configure(text = "Off")
        else:
            self.log.insert(tk.END, self.buffer.rstrip() + "\n")

    def updateTemperaturePlot(self, colorbar):
        # Simulate temperature updates
       #self.temperatures += np.random.randn(*self.temperatures.shape) * 0.1
        
        rbf = Rbf(self.points[:, 0], self.points[:, 1], self.temperatures, function='multiquadric', smooth=0)
        grid_x, grid_y = np.mgrid[0.75:3:100j, 0:1:100j]
        grid_z = rbf(grid_x, grid_y)
        
        self.ax.clear()
        im = self.ax.imshow(grid_z.T, extent=(0.75,3,0,1), origin='lower', cmap='coolwarm', vmin=0, vmax=100)
        if(colorbar):
            plt.colorbar(im, label='Temperature (°C)')
        self.ax.scatter(self.points[:,0], self.points[:,1], c='black', s=50)  # Measurement points
        self.canvas.draw()
               
    def recursive_update_textbox(self, start):
        if self.timer == 10:
            self.log.insert(tk.END, "Alive and Connected \n")
            self.timer = 0
            
        if (start):
            self.log.insert(tk.END, 'Log File: TestData/Test_' + self.start_dt + '.csv\n')
            
        if not self.serialPortManager.read_buffer():
            pass
        else:
            self.buffer = self.serialPortManager.read_buffer()
            self.updateTemperatures()
            now = datetime.now()
            dt_string = now.strftime("%Y/%m/%d %H:%M:%S ")
            
            self.datetimeData.configure(text = dt_string)
                
            if self.logDataVar.get():
                # The checkbox is checked, proceed with logging
                with open('TestData/Test_' + self.start_dt + ".csv", 'a', newline='\n' ) as file:
                    writer = csv.writer(file,quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([dt_string + self.buffer.strip()])
                    
            self.updateTemperaturePlot(False)
        
        # autoscroll to the bottom
        self.log.see(tk.END)
        # Recursively call recursive_update_textbox using Tkinter after() method
        if self.serialPortManager.isRunning:
            self.window.after(self.guiUpdateInterval, self.recursive_update_textbox, False)
            self.timer = self.timer + 1

    def get_available_serial_ports(self):
        # Clear portNames list
        portNames = []
        # Get a list of available serial ports
        portsList = list_ports.comports()
        # Sort based on port names
        portsList = sorted(portsList)

        for port in portsList:
            portNames.append(port.device)

        return portNames  
    
    # def create_db_and_table(self):
    #     # Connect to SQLite database (or create it if it doesn't exist)
    #     conn = sqlite3.connect('calibration_data.db')
    #     c = conn.cursor()

    #     # Create table
    #     c.execute('''CREATE TABLE IF NOT EXISTS calibration
    #                 (TSA INTEGER PRIMARY KEY, raw_low REAL, ref_low REAL, raw_high REAL, ref_high REAL)''')
    #     conn.commit()
    #     conn.close()
    
    # def insert_calibration_data(self, TSA, raw_low, ref_low, raw_high, ref_high):
    #     conn = sqlite3.connect('calibration_data.db')
    #     c = conn.cursor()
    #     c.execute('''INSERT OR REPLACE INTO calibration (TSA, raw_low, ref_low, raw_high, ref_high)
    #                 VALUES (?, ?, ?, ?, ?)''', (TSA, raw_low, ref_low, raw_high, ref_high))
    #     conn.commit()
    #     conn.close()
    
    # def get_calibration_data(self, TSA):
    #     conn = sqlite3.connect('calibration_data.db')
    #     c = conn.cursor()
    #     c.execute('''SELECT * FROM calibration WHERE TSA=?''', (TSA,))
    #     data = c.fetchone()
    #     conn.close()
    #     return data  # data is a tuple: (TSA, raw_low, ref_low, raw_high, ref_high)
        
    def create_db_and_table(self):
        # Connect to SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()

        # Modify the table creation query to include calibration data for each sensor
        c.execute('''CREATE TABLE IF NOT EXISTS calibration
                    (TSA INTEGER PRIMARY KEY,
                    raw_low_ta1 REAL, ref_low_ta1 REAL, raw_high_ta1 REAL, ref_high_ta1 REAL,
                    raw_low_ta2 REAL, ref_low_ta2 REAL, raw_high_ta2 REAL, ref_high_ta2 REAL,
                    raw_low_ta3 REAL, ref_low_ta3 REAL, raw_high_ta3 REAL, ref_high_ta3 REAL,
                    raw_low_ta4 REAL, ref_low_ta4 REAL, raw_high_ta4 REAL, ref_high_ta4 REAL,
                    raw_low_ta5 REAL, ref_low_ta5 REAL, raw_high_ta5 REAL, ref_high_ta5 REAL,
                    raw_low_ta6 REAL, ref_low_ta6 REAL, raw_high_ta6 REAL, ref_high_ta6 REAL)''')
        conn.commit()
        conn.close()
        
    def insert_calibration_data(self, TSA, data):
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()
        # Assuming 'data' is a dictionary containing calibration for each sensor
        c.execute('''INSERT OR REPLACE INTO calibration (TSA,
                    raw_low_ta1, ref_low_ta1, raw_high_ta1, ref_high_ta1,
                    raw_low_ta2, ref_low_ta2, raw_high_ta2, ref_high_ta2,
                    raw_low_ta3, ref_low_ta3, raw_high_ta3, ref_high_ta3,
                    raw_low_ta4, ref_low_ta4, raw_high_ta4, ref_high_ta4,
                    raw_low_ta5, ref_low_ta5, raw_high_ta5, ref_high_ta5,
                    raw_low_ta6, ref_low_ta6, raw_high_ta6, ref_high_ta6)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (TSA,
                    data['raw_low_ta1'], data['ref_low_ta1'], data['raw_high_ta1'], data['ref_high_ta1'],
                    data['raw_low_ta2'], data['ref_low_ta2'], data['raw_high_ta2'], data['ref_high_ta2'],
                    data['raw_low_ta3'], data['ref_low_ta3'], data['raw_high_ta3'], data['ref_high_ta3'],
                    data['raw_low_ta4'], data['ref_low_ta4'], data['raw_high_ta4'], data['ref_high_ta4'],
                    data['raw_low_ta5'], data['ref_low_ta5'], data['raw_high_ta5'], data['ref_high_ta5'],
                    data['raw_low_ta6'], data['ref_low_ta6'], data['raw_high_ta6'], data['ref_high_ta6']))
        
        conn.commit()
        conn.close()
        
    def get_calibration_data(self, TSA):
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()
        c.execute('''SELECT * FROM calibration WHERE TSA=?''', (TSA,))
        data = c.fetchone()
        conn.close()
        # Convert the row to a more usable format if desired
        return data
        
    def load_thermistor_sensor_assembly(self, tsaID):
        # Connect to the database
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()

        # Query to fetch the calibration data for TSA with a specific ID, e.g., 1
        tsa_id = tsaID  # Example TSA ID
        c.execute("SELECT * FROM calibration WHERE TSA=?", (tsa_id,))
        data = c.fetchone()
        conn.close()

        if not data:
            print("No calibration data found for the specified TSA.")
            return None

        # Create TSA object
        tsa = ThermistorSensorAssembly()

        # Assuming the database returns data in the same order as columns were defined
        # And that the ThermistorSensor's set_calibration_data method accepts a single dictionary
        for i, sensor_id in enumerate(tsa.sensors.keys()):
            calibration_data = {
                'raw_low': data[i * 4 + 1],  # Adjust indices based on actual database schema
                'ref_low': data[i * 4 + 2],
                'raw_high': data[i * 4 + 3],
                'ref_high': data[i * 4 + 4],
            }
            tsa.sensors[sensor_id].set_calibration_data(**calibration_data)

        return tsa

    def open_calibration_window(self):
        # Create a new top-level window
        calibration_window = tk.Toplevel(self.window)
        calibration_window.title("Calibration Settings")

        # Display the current TSA
        current_tsa_label = tk.Label(calibration_window, text=f"Current TSA: {int(self.tsaVar.get())}")
        current_tsa_label.pack()

        # Entry fields
        labels = ['Raw Low', 'Ref Low', 'Raw High', 'Ref High']
        self.entries = {}
        for label in labels:
            frame = tk.Frame(calibration_window)
            frame.pack(fill=tk.X, padx=5, pady=5)
            lbl = tk.Label(frame, text=label, width=20)
            lbl.pack(side=tk.LEFT)
            entry = tk.Entry(frame)
            entry.pack(fill=tk.X, padx=5, expand=True)
            self.entries[label.lower().replace(" ", "_")] = entry
            
        currentCal = self.get_calibration_data(int(self.tsaVar.get()))                                
                                               
        self.entries['raw_low'].insert(0,currentCal[1])
        self.entries['ref_low'].insert(0,currentCal[2])
        self.entries['raw_high'].insert(0,currentCal[3])
        self.entries['ref_high'].insert(0,currentCal[4])
            
        # Calibrate button
        calibrate_button = tk.Button(calibration_window, text="Calibrate", command=self.save_calibration_data)
        calibrate_button.pack(pady=10)
            
    def save_calibration_data(self):
        # Retrieve entry values
        raw_low = self.entries['raw_low'].get()
        ref_low = self.entries['ref_low'].get()
        raw_high = self.entries['raw_high'].get()
        ref_high = self.entries['ref_high'].get()
        
        # Convert to appropriate types (float) and handle conversion errors if necessary
        try:
            raw_low, ref_low, raw_high, ref_high = map(float, [raw_low, ref_low, raw_high, ref_high])
        except ValueError:
            # Handle error, e.g., show an error message
            tk.messagebox.showerror("Error", "Please enter valid numbers for calibration.")
            return

        # Assuming self.selectedTSA holds the current TSA value
        TSA = int(self.tsaVar.get())
        
        # Save to database
        self.insert_calibration_data(TSA, raw_low, ref_low, raw_high, ref_high)
        
        tk.messagebox.showinfo("Success", "Calibration data saved successfully.")
    
    def on_close(self):
        # Stop the serial port manager
        if self.serialPortManager.isRunning:
            self.serialPortManager.stop()
        # Destroy the window
        self.ledIndicator.config(bg="red")  # Ensure LED is red
        self.window.destroy()          
            
class SerialPortManager:
    def __init__(self, serialPortBaud=9600):
        self.now = datetime.now()
        self.isRunning = False
        self.serialPortName = None
        self.serialPortBaud = serialPortBaud
        self.serialPort = serial.Serial()
        self.serialPortBuffer = ""
    
    def start(self):
        self.isRunning = True
        try:
            if self.serialPort is None or not self.serialPort.isOpen():
                self.serialPort = serial.Serial(port=self.serialPortName, baudrate=self.serialPortBaud, timeout=2)
            self.serialPortThread = threading.Thread(target=self.thread_handler)
            self.serialPortThread.daemon = True  # Set the thread as a daemon
            self.serialPortThread.start()
        except Exception as e:
            self.isRunning = False
            raise Exception(f"Failed to open serial port: {e}")

    def stop(self):
        self.isRunning = False
        if hasattr(self, 'serialPortThread') and self.serialPortThread.is_alive():
            self.serialPortThread.join()
        if self.serialPort and self.serialPort.isOpen():
            self.serialPort.close()

    def set_name(self, serialPortName):
        self.serialPortName = serialPortName
        
    def send_serial(self, data):
        if self.isRunning:
            try:
                # print("Sending" + str(data))
                self.serialPort.write(data.encode())
            except serial.serialutil.SerialTimeoutException:
                self.console_buffer.text += 'write timeout\n'
            except ValueError:
                self.console_buffer.text += 'Wrong hex data format in send area, cannot transfer to ASCII\n'
            
    def thread_handler(self):
        while self.isRunning:
            if self.serialPort.isOpen():
                try:
                    # Read data
                    self.serialPortBuffer = self.serialPort.readline().decode("utf-8")
                except Exception as e:
                    print(f"Error reading from serial port: {e}")
            else:
                break  # Exit loop if the port is closed


    def read_buffer(self):
        # Return a copy of serial port buffer
        return self.serialPortBuffer

    def __del__(self):
        if self.serialPort.isOpen():
            self.serialPort.close()
        
class ThermistorSensor:
    def __init__(self, identifier, raw_low=0.0, ref_low=0.0, raw_high=0.0, ref_high=0.0):
        self.identifier = identifier
        self.calibration_data = {
            'raw_low': raw_low,
            'ref_low': ref_low,
            'raw_high': raw_high,
            'ref_high': ref_high
        }

    def set_calibration_data(self, raw_low, ref_low, raw_high, ref_high):
        self.calibration_data['raw_low'] = raw_low
        self.calibration_data['ref_low'] = ref_low
        self.calibration_data['raw_high'] = raw_high
        self.calibration_data['ref_high'] = ref_high

    def get_calibration_data(self):
        return self.calibration_data

    def __repr__(self):
        return f"ThermistorSensor(ID: {self.identifier}, Calibration: {self.calibration_data})"        
        
class ThermistorSensorAssembly:
    def __init__(self, identifier):
        self.identifier = identifier
        self.sensors = {f"ta{i+1}": ThermistorSensor(f"ta{i+1}") for i in range(6)}

    def set_sensor_calibration(self, sensor_id, raw_low, ref_low, raw_high, ref_high):
        if sensor_id in self.sensors:
            self.sensors[sensor_id].set_calibration_data(raw_low, ref_low, raw_high, ref_high)
        else:
            print(f"Sensor {sensor_id} not found in assembly.")

    def get_sensor_calibration(self, sensor_id):
        if sensor_id in self.sensors:
            return self.sensors[sensor_id].get_calibration_data()
        else:
            print(f"Sensor {sensor_id} not found in assembly.")
            return None

    def __repr__(self):
        return f"ThermistorSensorAssembly(Sensors: {list(self.sensors.keys())})"
  
if __name__ == "__main__":
    app = GUI("On-Instrument Slide Temperature Measurement System")
    app.window.mainloop()
