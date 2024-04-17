"""
Title: On-Instrument Slide Temperature Measurement System GUI
Version: 2.2
Author: Nestor Garcia
Date: 01 Apr 24
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
import threading
from datetime import datetime
import csv
import os
import json
from serial.tools import list_ports
import sqlite3
import serial
from collections import deque

ICON_PATH = os.path.join(os.path.dirname(__file__), "ENGR498_Logo.png")

class GUI:
# Initilization
    def __init__(self, title):
        self.window = tk.Tk()
        self.window.title(title)
        self.setup_icon()
        
        self.isStarted = False
        self.start_dt = datetime.now().strftime("%Y_%m_%d_%H:%M")
        self.guiUpdateInterval = 1000
        
        self.sample_count = 0
        self.max_samples = 3
        # Initialize temperature_buffers with deques for efficient pop/append operations
        self.temperature_buffers = [deque(maxlen=self.max_samples) for _ in range(7)]
        
        self.setup_variables()
        self.create_widgets()
        self.setup_serial_port_manager()
        self.create_db_and_table()
        
        self.setup_plots()

        # Bind the close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

# Setup Functions
    def setup_icon(self):
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.window.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
        except Exception as e:
            self.log_message(f"Error setting icon: {e}")

    def setup_variables(self):
        self.portNamesList = []
        self.tsaList = [1, 2, 3, 4, 5, 6]
        self.tsaSelect = 1
        self.points = np.array([(1.125, 0.75), (2.625, 0.75), (1.5750, 0.5), (2.125, 0.5), (1.125, 0.25), (2.625, 0.25)])
        self.temperatures = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
 
    def create_widgets(self):
        self.create_controls_frame()
        self.create_temperature_display()
        self.create_console()

 # Widget Creation
    def create_controls_frame(self):
        self.topFrame = tk.Frame(self.window, bg="#303030")
        self.topFrame.pack(side=tk.TOP, fill=tk.X)

        # Scan button
        self.scanButton = tk.Button(self.topFrame, text="Scan", command=self.scan_ports)
        self.scanButton.pack(side=tk.LEFT, padx=20, pady=20)

        # Ports Label
        self.portsLabel = tk.Label(self.topFrame, text="Ports", bg="#303030", fg="white")
        self.portsLabel.pack(side=tk.LEFT, padx=5, pady=20)
        
        # Serial port selection dropdown
        self.selectedPort = tk.StringVar()
        self.portDropdown = ttk.Combobox(self.topFrame, textvariable=self.selectedPort, values=self.portNamesList, state='readonly')
        self.portDropdown.pack(side=tk.LEFT, padx=5, pady=20)
        self.portDropdown.bind('<<ComboboxSelected>>', self.on_combobox_select)

        # TSA Select Label
        self.tsaLabel = tk.Label(self.topFrame, text="TSA Select", bg="#303030", fg="white")
        self.tsaLabel.pack(side=tk.LEFT, padx=5, pady=20)
        
        # TSA Select dropdown
        self.tsaVar = tk.StringVar(self.window)
        self.tsaDropdown = ttk.Combobox(self.topFrame, textvariable=self.tsaVar, values=self.tsaList, state='readonly')
        self.tsaDropdown.pack(side=tk.LEFT, padx=5, pady=20)
        self.tsaDropdown.bind('<<ComboboxSelected>>', self.on_combobox_select)
        self.tsaDropdown.set(self.tsaList[0])

        # Calibrate Button
        self.calibrateButton = tk.Button(self.topFrame, text="Calibrate", command=self.open_calibration_window)
        self.calibrateButton.pack(side=tk.LEFT, padx=(5, 5), pady=20)
        
        # Calibration On Checkbox
        self.calOnVar = tk.BooleanVar()
        self.calOnCheckbox = tk.Checkbutton(self.topFrame, text="Cal On", variable=self.calOnVar, onvalue=True, offvalue=False, bg="#303030", fg="white")
        self.calOnCheckbox.pack(side=tk.LEFT, padx=(5, 5), pady=20)

        # Log Data Checkbox
        self.logDataVar = tk.BooleanVar()
        self.logDataCheckbox = tk.Checkbutton(self.topFrame, text="Log Data", variable=self.logDataVar, onvalue=True, offvalue=False, bg="#303030", fg="white", command=self.logStatus)
        self.logDataCheckbox.pack(side=tk.LEFT, padx=(5, 5), pady=20)
        self.logDataCheckbox.config(state="disabled")

        # Ref On Checkbox
        self.refOnVar = tk.BooleanVar()
        self.refOnCheckbox = tk.Checkbutton(self.topFrame, text="Ref On", variable=self.refOnVar, onvalue=True, offvalue=False, bg="#303030", fg="white", command=self.refStatus)
        self.refOnCheckbox.pack(side=tk.LEFT, padx=(5, 5), pady=20)
        self.refOnCheckbox.config(state="disabled")

        
        # LED indicator
        self.ledIndicator = tk.Canvas(self.topFrame, width=20, height=20, bg="#303030", highlightthickness=0)
        self.ledCircle = self.ledIndicator.create_oval(2, 2, 18, 18, fill="red")
        self.ledIndicator.pack(side=tk.LEFT, padx=(50, 0), pady=20)
        
        # Connect button
        self.connectButton = tk.Button(self.topFrame, text="Connect", command=self.connect)
        self.connectButton.pack(side=tk.LEFT, padx=(10, 40), pady=20)

    def create_temperature_display(self):
        # Header frame for the title and clock
        self.headerFrame = tk.Frame(self.window, bg="#ffffff")
        self.headerFrame.pack(side=tk.TOP, fill=tk.X, expand=False, padx=0, pady=0)

        # "Temperatures" title in the header frame, centered
        self.temperaturesTitle = tk.Label(self.headerFrame, text="Temperatures", font=("Helvetica", 24, 'bold'), fg="#000000", bg="#ffffff")
        self.temperaturesTitle.pack(side=tk.BOTTOM, expand=True)

        # Datetime display in the header frame, aligned to the right
        self.datetimeData = tk.Label(self.headerFrame, text="0.00", font=("Helvetica", 20), bg="#ffffff", fg="#000000")
        self.datetimeData.pack(side=tk.RIGHT, padx=5)
        self.datetimeLabel = tk.Label(self.headerFrame, text="Datetime:", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg="#000000")
        self.datetimeLabel.pack(side=tk.RIGHT, padx=0)

        # LabelFrame for temperature sensors and their values
        self.temperatureDataBox = tk.LabelFrame(self.window, labelanchor='n', bd=0, bg="#ffffff")
        self.temperatureDataBox.pack(side=tk.TOP, fill=tk.X, expand=True, padx=0, pady=0)

        # Configure the columns to have equal weight for even spacing
        for col in range(5):
            self.temperatureDataBox.columnconfigure(col, weight=1)
        self.temperatureDataBox.columnconfigure(5, weight=2)

        # Specific placement for each thermistor and its temperature label
        placements = [
            (0, 0),  # T1 in row 1, column 1
            (0, 4),  # T2 in row 1, column 4
            (1, 1),  # T3 in row 2, column 2
            (1, 3),  # T4 in row 2, column 3
            (2, 0),  # T5 in row 3, column 1
            (2, 4)   # T6 in row 3, column 4
        ]
        self.temp_label = [None] * 6  # Initialize the list to store temperature labels

        for i, (row, col) in enumerate(placements):
            # Create and place the thermistor label
            self.thermistor_label = tk.Label(self.temperatureDataBox, text=f"T{i+1}:", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg="#000000")
            self.thermistor_label.grid(row=row, column=col, sticky="e", padx=5, pady=5)

            # Create and place the temperature label directly next to the thermistor label
            self.temp_label[i] = tk.Label(self.temperatureDataBox, text="0.00°C", font=("Helvetica", 20), bg="#ffffff", fg="#000000")
            self.temp_label[i].grid(row=row, column=col+1, sticky="w", padx=5, pady=5)

        # Placement for reference labels
        self.refLabel = tk.Label(self.temperatureDataBox, text="Ref:", font=("Helvetica", 20, 'bold'), bg="#ffffff", fg="#000000")
        self.refLabel.grid(row=3, column=2, sticky="e", padx=0, pady=5)

        self.refTempLabel = tk.Label(self.temperatureDataBox, text="Off", font=("Helvetica", 20), bg="#ffffff", fg="#000000")
        self.refTempLabel.grid(row=3, column=3, sticky="w", padx=0, pady=5)

    def create_console(self):
        self.log = scrolledtext.ScrolledText(self.window, height=10)
        self.log.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_plots(self):
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1, pady=5)
        self.updateTemperaturePlot(True)

# Event Handlers & Callbacks
    def on_combobox_select(self, event=None):
        """
        Event handler called when an item is selected in the combobox.
        It changes the focus to the main window to prevent the combobox from trapping the focus.
        """
        self.window.focus_set()

    def refStatus(self):
        if(self.refOnVar.get()):
            self.serialPortManager.send_serial("REF ON")
        else:
            self.serialPortManager.send_serial("REF OFF")
    
    def logStatus(self): 
        if(self.logDataVar.get()):
            self.log.insert(tk.END, f"Logging On: Log File - temperature_data_TSA{self.tsaVar.get()}_{self.start_dt}.csv\n")  # Add to GUI log
 
    # def handle_data_received(self, data):
    #     """
    #     This method gets called by SerialPortManager with new data.
    #     It parses the JSON data and updates the GUI with the temperatures.
    #     """
    #     time_dt = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    #     self.datetimeData.configure(text = time_dt)
    #     try:            
    #         # Extract temperature data and update GUI
    #         if "temps" in data:
                
    #             temperatures = data["temps"]
    #             self.temperatures = temperatures[:6]
    #             self.updateTemperatures(temperatures)
                
    #             # Log the received data for debugging
    #             # self.log.insert(tk.END, f"Data received: {data}\n")
    #             # self.log.see(tk.END)
    #         elif "type" in data and "message" in data:  # Check if it's a log message
    #             log_message = f"{data['type']}: {data['message']}"
    #             # print(log_message)  # Print to console or append to a log file
    #             self.log.insert(tk.END, time_dt + " - " + log_message + "\n")  # Add to GUI log
        
    #     except json.JSONDecodeError:
    #         # If there's an error in parsing JSON, log the error for debugging
    #         self.log.insert(tk.END, "Failed to parse JSON from incoming data.\n")
    #         self.log.see(tk.END)
 
    def handle_data_received(self, data):
        """
        Optimized to accumulate data and update GUI more efficiently.
        """
        time_dt = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.datetimeData.configure(text=time_dt)
        try:
            if "temps" in data:
                temperatures = data["temps"][:7]  # Assuming data for 7 sensors, including reference.

                # Append temperatures to their respective buffers
                for i, temp in enumerate(temperatures):
                    self.temperature_buffers[i].append(temp)
                
                self.sample_count += 1
                
                # If enough samples have been collected, average and update GUI
                if self.sample_count == self.max_samples:
                    self.sample_count = 0  # Reset sample counter
                    averaged_temperatures = [sum(buff) / self.max_samples for buff in self.temperature_buffers]

                    # Update GUI and log data
                    self.updateTemperatures(averaged_temperatures)
                    
            elif "type" in data and "message" in data:
                log_message = f"{data['type']}: {data['message']}"
                self.log.insert(tk.END, time_dt + " - " + log_message + "\n")
                
        except json.JSONDecodeError:
            self.log.insert(tk.END, "Failed to parse JSON from incoming data.\n")
            self.log.see(tk.END)
 
    def handle_message(self, message):
        self.log.insert(tk.END, message + "\n")
   
# Serial Port Management
    def scan_ports(self):
        threading.Thread(target=self.scan_ports_thread, daemon=True).start()

    def scan_ports_thread(self):

        self.log.insert(tk.END, "Scanning ports...\n")
        # Get a list of available serial ports
        portNamesList = self.get_available_serial_ports()

        if not portNamesList:
            portNamesList = ["No ports available"]
            # Ensure GUI updates happen from the main thread
            self.window.after(0, self.portDropdown.configure, {'state': 'disabled'})
            self.window.after(0, self.tsaDropdown.configure, {'state': 'disabled'})
            self.window.after(0, self.connectButton.configure, {'state': 'disabled'})
        else:
            self.isAnyPortAvailable = True
            # Ensure GUI updates happen from the main thread
            self.window.after(0, self.portDropdown.configure, {'state': 'readonly'})
            self.window.after(0, self.tsaDropdown.configure, {'state': 'readonly'})
            self.window.after(0, lambda: self.connectButton.configure(state='normal' if self.isStarted else 'normal'))

        # Update the dropdown menu with the new list of ports
        self.window.after(0, self.update_option_menu, portNamesList)
    
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
    
    def update_option_menu(self, portNames):
        # Remove old items
        self.portDropdown.delete(0, "end")
        # Set default value of selectedPort
        self.portDropdown['values'] = portNames
        self.selectedPort.set(portNames[0])
    
    def setup_serial_port_manager(self):
        # self.serialPortManager = self.serialPortManager = SerialPortManager(data_received_callback=self.handle_data_received, message_callback=self.handle_message)
        self.serialPortManager = SerialPortManager(callbacks={'data_received': self.handle_data_received,
                                                              'message': self.handle_message})
   
    def connect(self):
        if not self.isStarted:
            self.log.insert(tk.END, "Connecting...\n")
            self.serialPortName = self.selectedPort.get()
            self.tsa_select()

            self.serialPortManager.stop()  # Ensure any previous connection is closed
            self.serialPortManager.set_name(self.serialPortName)
            success, error_message = self.serialPortManager.start()
            if success:
                # Connection was successful
                self.log.insert(tk.END, f"Connected to: {self.serialPortName}\n")
                self.setup_after_connection()
            else:
                # Connection failed, display the error message from `start`
                self.log.insert(tk.END, error_message + "\n")
                self.teardown_after_disconnection()
        else:
            # Disconnecting
            self.teardown_after_disconnection()
            self.serialPortManager.stop()
            self.log.insert(tk.END, "Disconnected.\n")

# Temperature & Plotting
    def updateTemperaturePlot(self, colorbar):
        """
        Updates the temperature distribution plot.
        :param colorbar: A boolean indicating whether to display the colorbar.
        """
        # Generate radial basis function (RBF) interpolator for the temperature points
        rbf = Rbf(self.points[:, 0], self.points[:, 1], self.temperatures, function='multiquadric', smooth=0)
        # Create a grid to evaluate the RBF over
        grid_x, grid_y = np.mgrid[0.75:3:100j, 0:1:100j]
        grid_z = rbf(grid_x, grid_y)
        
        self.ax.clear()  # Clear the current plot to update it with new data
        # Display the interpolated temperature data
        im = self.ax.imshow(grid_z.T, extent=(0.75,3,0,1), origin='lower', cmap='coolwarm', vmin=0, vmax=100)
        # Add colorbar if specified
        if colorbar:
            plt.colorbar(im, ax=self.ax, label='Temperature (°C)')
        # Scatter plot to show the actual measurement points
        self.ax.scatter(self.points[:, 0], self.points[:, 1], c='black', s=50, zorder=5)
        self.canvas.draw()  # Redraw the canvas with the updated plot

    def updateTemperatures(self, temperatures):
        """
        Updates the GUI labels with the new temperature data.
        """
        print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        for i, temp in enumerate(temperatures):
            # Ensure we do not update more labels than we have
            if i < len(self.temp_label):
                # Update the label with the new temperature
                if self.calOnVar.get():
                    cal_temp = self.TSA.get_calibrated_temp(f"t{i+1}",temp)
                else:
                    cal_temp = temp
                self.temp_label[i].configure(text=f"{cal_temp:.2f}°C")
    
            # If you have a reference temperature to update
            if self.refOnVar.get() and i == len(temperatures) - 1:  # Assuming the last value is the reference temperature
                self.refTempLabel.configure(text=f"{temp:.2f}°C")
            else:
                self.refTempLabel.configure(text="Off")
        self.temperatures = temperatures[:6]
        self.updateTemperaturePlot(False)
        
        if self.logDataVar.get():
            self.log_temperatures_to_csv(temperatures)

# Calibration & Database
    def create_db_and_table(self):
        """
        Creates a SQLite database and a table for storing calibration data if they don't exist.
        """
        # Connect to SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()

        # Create a table for calibration data if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS calibration
                    (TSA INTEGER PRIMARY KEY,
                    raw_low_t1 REAL, ref_low_t1 REAL, raw_high_t1 REAL, ref_high_t1 REAL,
                    raw_low_t2 REAL, ref_low_t2 REAL, raw_high_t2 REAL, ref_high_t2 REAL,
                    raw_low_t3 REAL, ref_low_t3 REAL, raw_high_t3 REAL, ref_high_t3 REAL,
                    raw_low_t4 REAL, ref_low_t4 REAL, raw_high_t4 REAL, ref_high_t4 REAL,
                    raw_low_t5 REAL, ref_low_t5 REAL, raw_high_t5 REAL, ref_high_t5 REAL,
                    raw_low_t6 REAL, ref_low_t6 REAL, raw_high_t6 REAL, ref_high_t6 REAL)''')

        # Commit the changes and close the connection to the database
        conn.commit()
        conn.close()

    def load_thermistor_sensor_assembly(self, tsa_id=1):
        """
        Loads calibration data for a specified Thermistor Sensor Assembly (TSA) from the database.
        :param tsa_id: The ID of the TSA for which to load calibration data.
        :return: A ThermistorSensorAssembly object with loaded calibration data.
        """
        # Initialize default calibration data in case no data is found in the database
        default_calibration = {'raw_low': 0.00, 'ref_low': 25.0, 'raw_high': 100.00, 'ref_high': 100.0}
        
        # Create TSA object with default calibration data for each sensor
        tsa = ThermistorSensorAssembly(tsa_id)
        for sensor_id in tsa.sensors.keys():
            tsa.set_sensor_calibration(sensor_id, **default_calibration)

        # Connect to the database
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()

        # Query to fetch the calibration data for the specified TSA
        try:
            c.execute("SELECT * FROM calibration WHERE TSA=?", (tsa_id,))
            data = c.fetchone()

            if data:
                # Load calibration data from the database into the TSA
                keys = list(tsa.sensors.keys())
                for i, sensor_id in enumerate(keys):
                    idx = i * 4 + 1  # Calculate the index offset based on the column order
                    calibration_data = {
                        'raw_low': data[idx],
                        'ref_low': data[idx + 1],
                        'raw_high': data[idx + 2],
                        'ref_high': data[idx + 3]
                    }
                    tsa.set_sensor_calibration(sensor_id, **calibration_data)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error loading TSA calibration data: {e}")
        finally:
            conn.close()  # Ensure the database connection is closed even if an error occurs

        return tsa

    def save_calibration_data(self):
        # Prepare data for database update
        flat_calibration_data = {}
        for sensor_id, entries in self.calibration_entries.items():
            for cal_point, entry in entries.items():
                # Construct the new key by removing 'ta' and adding 't' prefix
                new_key = f"{cal_point}_{sensor_id.replace('ta', 't')}"
                flat_calibration_data[new_key] = float(entry.get())

        # Assuming TSA ID is 1 for simplicity
        self.insert_calibration_data(self.tsaSelect, flat_calibration_data)
        tk.messagebox.showinfo("Success", "Calibration data saved successfully.")   

    def insert_calibration_data(self, TSA, data):
        print(data)
        conn = sqlite3.connect('calibration_data.db')
        c = conn.cursor()
        # Assuming 'data' is a dictionary containing calibration for each sensor
        c.execute('''INSERT OR REPLACE INTO calibration (TSA,
                    raw_low_t1, ref_low_t1, raw_high_t1, ref_high_t1,
                    raw_low_t2, ref_low_t2, raw_high_t2, ref_high_t2,
                    raw_low_t3, ref_low_t3, raw_high_t3, ref_high_t3,
                    raw_low_t4, ref_low_t4, raw_high_t4, ref_high_t4,
                    raw_low_t5, ref_low_t5, raw_high_t5, ref_high_t5,
                    raw_low_t6, ref_low_t6, raw_high_t6, ref_high_t6)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (TSA,
                    data['raw_low_t1'], data['ref_low_t1'], data['raw_high_t1'], data['ref_high_t1'],
                    data['raw_low_t2'], data['ref_low_t2'], data['raw_high_t2'], data['ref_high_t2'],
                    data['raw_low_t3'], data['ref_low_t3'], data['raw_high_t3'], data['ref_high_t3'],
                    data['raw_low_t4'], data['ref_low_t4'], data['raw_high_t4'], data['ref_high_t4'],
                    data['raw_low_t5'], data['ref_low_t5'], data['raw_high_t5'], data['ref_high_t5'],
                    data['raw_low_t6'], data['ref_low_t6'], data['raw_high_t6'], data['ref_high_t6']))
        
        conn.commit()
        conn.close()

    def open_calibration_window(self):
        """
        Opens a new window for calibration settings, allowing users to view and modify calibration data for sensors.
        """
        self.tsa_select()  # Update the selected TSA based on user input from the main window
        calibration_window = tk.Toplevel(self.window)
        calibration_window.title(f"Calibration Settings: TSA {self.TSA.get_ID()}")

        self.calibration_entries = {}  # Dictionary to store entry widgets for calibration data

        for sensor_id in range(1, 7):  # Assuming 6 sensors, named t1 through t6
            # Create a frame for each sensor's calibration settings
            frame = tk.Frame(calibration_window)
            frame.pack(fill=tk.X, padx=5, pady=5)
            label = tk.Label(frame, text=f"Sensor T{sensor_id}", width=20)
            label.pack(side=tk.LEFT)

            entries = {}
            # Create entry widgets for raw low, ref low, raw high, ref high calibration points
            for data_point in ['raw_low', 'ref_low', 'raw_high', 'ref_high']:
                entry_frame = tk.Frame(calibration_window)
                entry_frame.pack(fill=tk.X, padx=5, pady=2)
                lbl = tk.Label(entry_frame, text=data_point.replace('_', ' ').title(), width=10)
                lbl.pack(side=tk.LEFT)
                entry = tk.Entry(entry_frame)
                entry.pack(fill=tk.X, padx=5, expand=True)
                entries[data_point] = entry

            # Load current calibration data into the entry widgets
            current_calibration = self.TSA.get_sensor_calibration(f"t{sensor_id}")
            entries['raw_low'].insert(0, current_calibration['raw_low'])
            entries['ref_low'].insert(0, current_calibration['ref_low'])
            entries['raw_high'].insert(0, current_calibration['raw_high'])
            entries['ref_high'].insert(0, current_calibration['ref_high'])
            self.calibration_entries[f"t{sensor_id}"] = entries

        # Save button to submit changes
        save_button = tk.Button(calibration_window, text="Save Calibration", command=self.save_calibration_data)
        save_button.pack(pady=10)

# Utility and Cleanup
    def log_message(self, message):
        self.log.insert(tk.END, f"{message}\n")
        self.log.see(tk.END)

    def tsa_select(self):
        self.tsaSelect = int(self.tsaVar.get())
        self.TSA = self.load_thermistor_sensor_assembly(self.tsaSelect)
 
    def log_temperatures_to_csv(self, temperatures, ref_temperature=None):
        filename = f"Tkinter_GUI/TestData/temperature_data_TSA{self.tsaVar.get()}_{self.start_dt}.csv"
        headers = ["Timestamp", "T1", "T2", "T3", "T4", "T5", "T6", "Ref"]
        cal_headers = [header for i in range(1, 7) for header in [f"Raw Low T{i}", f"Ref Low T{i}", f"Raw High T{i}", f"Ref High T{i}"]]
        
        headers += ["Calibration On"] + cal_headers + ["Calibrated T1", "Calibrated T2", "Calibrated T3", "Calibrated T4", "Calibrated T5", "Calibrated T6"]
        
        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(headers)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cal_on = "Yes" if self.calOnVar.get() else "No"
            row = [now] + temperatures + ["Off" if ref_temperature is None else ref_temperature] + [cal_on]
            
            cal_values = []
            calibrated_temperatures = []
            for sensor_id in range(1, 7):
                sensor_key = f"t{sensor_id}"
                if self.calOnVar.get():
                    raw_temp = temperatures[sensor_id - 1]
                    calibrated_temp = self.TSA.get_calibrated_temp(sensor_key, raw_temp)
                    calibrated_temperatures.append(calibrated_temp)
                    calibration_data = self.TSA.get_sensor_calibration(sensor_key)
                    cal_values += [calibration_data['raw_low'], calibration_data['ref_low'],
                                   calibration_data['raw_high'], calibration_data['ref_high']]
                else:
                    calibrated_temperatures.append("N/A")  # Placeholder when calibration is off
                    cal_values += ["N/A"] * 4  # Placeholder values when calibration is off
            
            row += cal_values + calibrated_temperatures
            
            writer.writerow(row)

    def setup_after_connection(self):
        # Indicate that the device is started
        self.isStarted = True
        # Enable the "Log Data" checkbox, indicating data can now be logged
        self.logDataCheckbox.config(state="normal")
        self.refOnCheckbox.config(state="normal")
        # Disable the calibration button, assuming calibration cannot be done while connected
        self.calibrateButton.config(state="disabled")
        # Change the "Connect" button to "Disconnect"
        self.connectButton.configure(text="Disconnect")
        # Change the LED indicator to green, indicating an active connection
        self.ledIndicator.itemconfig(self.ledCircle, fill="green")
        # Any additional setup steps can be added here
        
    def teardown_after_disconnection(self):
        # Indicate that the device is no longer started
        self.isStarted = False
        # Disable the "Log Data" checkbox as no data should be logged when disconnected
        self.logDataCheckbox.config(state="disabled")
        self.refOnCheckbox.config(state="disabled")
        # Enable the calibration button, assuming calibration can be done while disconnected
        self.calibrateButton.config(state="normal")
        # Change the "Disconnect" button back to "Connect"
        self.connectButton.configure(text="Connect")
        # Change the LED indicator to red, indicating no active connection
        self.ledIndicator.itemconfig(self.ledCircle, fill="red")
        # Any additional teardown steps can be added here

    def on_close(self):
        if self.serialPortManager.isRunning:
            self.serialPortManager.stop()
        self.window.destroy()


class SerialPortManager:
# Initialization
    def __init__(self, callbacks=None, serialPortBaud=9600):
        self.callbacks = callbacks if callbacks is not None else {}
        # self.data_received_callback = data_received_callback
        self.serialPortBaud = serialPortBaud
        self.serialPort = None
        self.serialPortName = ''
        self.isRunning = False
        self.read_thread = None
        self.threadStop = False  # Add a flag to signal the thread to stop

# Configuration and State Management
    def set_name(self, serialPortName):
        self.serialPortName = serialPortName

    def start(self):
        if self.isRunning or not self.serialPortName:
            return False, "Serial port is already running or no port selected."
        try:
            self.serialPort = serial.Serial(self.serialPortName, self.serialPortBaud, timeout=2)
            self.isRunning = True
            self.read_thread = threading.Thread(target=self.read_from_port, daemon=True)
            self.read_thread.start()
            return True, ""  # No error message needed on success
        except serial.SerialException as e:
            error_message = f"Failed to open serial port: {e}"
            print(error_message)
            return False, error_message

    def stop(self):
        if self.isRunning:
            self.isRunning = False
            
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=5)  # Wait for the thread to terminate, with a timeout
            
            try:
                if self.serialPort and self.serialPort.isOpen():
                    self.serialPort.close()
            except Exception as e:
                print(f"Error closing serial port: {e}")
            
            self.read_thread = None
            self.serialPort = None

    def send_serial(self, data):
        if self.isRunning and self.serialPort:
            try:
                self.serialPort.write(data.encode('utf-8'))
            except serial.SerialException as e:
                print(f"Error sending data: {e}")

# Data Handling
    def read_from_port(self):
        while self.isRunning:
            try:
                if self.serialPort.inWaiting() > 0:
                    line = self.serialPort.readline().decode('utf-8').strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.call_callback('data_received', data)
                        except json.JSONDecodeError as e:
                            self.call_callback('message', f"JSON Decode Error: {e}")
            except (OSError, serial.SerialException) as e:
                self.call_callback('message', f"Error reading from serial port: {e}")
                self.call_callback('message', "Disconnect and try again.")
                break  # or continue, depending on desired behavior
            
            # time.sleep(0.1)  # Adjust sleep time as needed

# Callback Management
    def set_callback(self, event_name, callback):
        self.callbacks[event_name] = callback
        
    def call_callback(self, event_name, *args, **kwargs):
        if event_name in self.callbacks:
            self.callbacks[event_name](*args, **kwargs)

# Utility
    def __del__(self):
        self.stop()


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
    
    def get_calibrated_temp(self, rawTemp):
        return (((rawTemp - self.calibration_data['raw_low']) * (self.calibration_data['ref_high'] - self.calibration_data['ref_low'])) / (self.calibration_data['raw_high'] - self.calibration_data['raw_low'])) + self.calibration_data['raw_low']

    def __repr__(self):
        return f"ThermistorSensor(ID: {self.identifier}, Calibration: {self.calibration_data})"        
        
class ThermistorSensorAssembly:
    def __init__(self, identifier):
        self.identifier = identifier
        self.sensors = {f"t{i+1}": ThermistorSensor(f"t{i+1}") for i in range(6)}

    def get_ID(self):
        return self.identifier
    
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
        
    def get_calibrated_temp(self, sensor_id, rawTemp):
        if sensor_id in self.sensors:
            return self.sensors[sensor_id].get_calibrated_temp(rawTemp)
        else:
            print(f"Sensor {sensor_id} not found in assembly.")
            return None

    def __repr__(self):
        return f"ThermistorSensorAssembly(Sensors: {list(self.sensors.keys())})"

if __name__ == "__main__":
    app = GUI("On-Instrument Slide Temperature Measurement System")
    app.window.mainloop()
