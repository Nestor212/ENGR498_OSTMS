"""
Title: On-Instrument Slide Temperature Measurement System GUI
Version: 4.1
Author: Nestor Garcia
Date: 08 Apr 24
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

Updates:
- Polynomial Calibration replaced 2-point calibration.
- Enhanced Real-Time Data Visualization with Live Linear Plotter.
- Database Enhancements.
- Updated User Interface controls.
- Refinements in Backend Operations.

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
from collections import deque
import subprocess
import sys
import OSTMS_TSA as TSA 
import OSTMS_serial as ser


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
        
        # Add a new button to run the OSTMS_Plotter script
        self.plotterButton = tk.Button(self.topFrame, text="Run Plotter", command=self.run_plotter_script)
        self.plotterButton.pack(side=tk.LEFT, padx=(10, 40), pady=20)

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
        self.tsaSelect = int(self.tsaVar.get())
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
        
    def run_plotter_script(self):
            script_filename = 'Tkinter_GUI/OSTMS_Plotter.py'
            # Start the script in a new thread to avoid freezing the GUI
            thread = threading.Thread(target=self.execute_script, args=(script_filename,))
            thread.start()

    def execute_script(self, script_filename):
        # Run the script using the same Python executable as the one running this script
        process = subprocess.Popen([sys.executable, script_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()  # Waits for the process to complete and gets the output
        
        # Log or display the output and errors
        if stdout:
            self.log_message(f"Output: {stdout}")
        if stderr:
            self.log_message(f"Error: {stderr}")

    def log_message(self, message):
        # Assuming you have a method to log messages to your GUI or console
        print(message)  # Change this to however you handle logging within your GUI
   
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
        self.serialPortManager = ser.SerialPortManager(callbacks={'data_received': self.handle_data_received,
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
        # print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
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
        conn = sqlite3.connect('poly_calibration_data.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS calibration
                    (TSA INTEGER PRIMARY KEY,
                    polynomial_coeffs_t1 TEXT, polynomial_coeffs_t2 TEXT,
                    polynomial_coeffs_t3 TEXT, polynomial_coeffs_t4 TEXT,
                    polynomial_coeffs_t5 TEXT, polynomial_coeffs_t6 TEXT)''')
        conn.commit()
        conn.close()

    def load_thermistor_sensor_assembly(self, tsa_id=1):
        conn = sqlite3.connect('poly_calibration_data.db')
        c = conn.cursor()
        tsa = TSA.ThermistorSensorAssembly(tsa_id)
        calibration_data = {}
        try:
            c.execute("SELECT * FROM calibration WHERE TSA=?", (tsa_id,))
            data = c.fetchone()
            if data:
                for i in range(1, 7):
                    coeffs_str = data[i]
                    coeffs = json.loads(coeffs_str) if coeffs_str else []
                    sensor_id = f"t{i}"
                    tsa.set_sensor_calibration(sensor_id, coeffs)
                    calibration_data[sensor_id] = coeffs_str
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
        return tsa, calibration_data  # Return both the assembly and calibration data



    def save_calibration_data(self):
        try:
            conn = sqlite3.connect('poly_calibration_data.db')
            c = conn.cursor()
            # Check if the entry exists
            c.execute("SELECT count(*) FROM calibration WHERE TSA=?", (self.tsaSelect,))
            exists = c.fetchone()[0]

            if not exists:
                # Insert a new row if TSA doesn't exist
                # Create placeholders for each polynomial_coeffs column
                placeholders = ', '.join(['?' for _ in range(6)])  # 6 coefficient columns
                # Add a placeholder for the TSA at the beginning
                c.execute(f"INSERT INTO calibration (TSA, polynomial_coeffs_t1, polynomial_coeffs_t2, polynomial_coeffs_t3, polynomial_coeffs_t4, polynomial_coeffs_t5, polynomial_coeffs_t6) VALUES (?, {placeholders})", (self.tsaSelect, '[]', '[]', '[]', '[]', '[]', '[]'))

            # Now, perform the update for each sensor
            for sensor_id in range(1, 7):
                raw_coeffs = self.calibration_entries[f"t{sensor_id}"].get()  # Get the string from the Entry widget
                try:
                    # Attempt to parse the string as a list; this also validates the format
                    coeffs_list = json.loads(raw_coeffs)
                    if not isinstance(coeffs_list, list):
                        raise ValueError("Coefficients must be in list format.")
                    # Convert list back to JSON string for storage
                    coeffs_json = json.dumps(coeffs_list)
                except json.JSONDecodeError:
                    tk.messagebox.showerror("Error", f"Invalid format for coefficients of sensor {sensor_id}. Please enter a valid JSON list.")
                    return
                except ValueError as e:
                    tk.messagebox.showerror("Error", str(e))
                    return

                column_name = f'polynomial_coeffs_t{sensor_id}'
                c.execute(f"UPDATE calibration SET {column_name} = ? WHERE TSA = ?", (coeffs_json, self.tsaSelect))

            conn.commit()
            conn.close()
            tk.messagebox.showinfo("Success", "Calibration data saved successfully.")
        except Exception as e:
            tk.messagebox.showerror("Error", str(e))

    def open_calibration_window(self):
        calibration_window = tk.Toplevel(self.window)
        calibration_window.title("Calibration Settings")
        calibration_window.geometry('600x400')

        self.calibration_entries = {}

        instructions = tk.Label(calibration_window, text="Enter the polynomial coefficients for each sensor.\n"
                                                        "Format: [a, b, c, ...] for ax^n + bx^(n-1) + cx^(n-2) + ...\n"
                                                        "Example: For a quadratic curve ax^2 + bx + c, enter '[a, b, c]'",
                                justify=tk.LEFT, padx=10)
        instructions.pack(pady=(5, 15))

        # Load existing calibration data
        _, existing_data = self.load_thermistor_sensor_assembly(self.tsaSelect)

        for sensor_id in range(1, 7):
            frame = tk.Frame(calibration_window)
            frame.pack(fill=tk.X, padx=5, pady=5)
            tk.Label(frame, text=f"Sensor {sensor_id} Coefficients:").pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=50)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.calibration_entries[f"t{sensor_id}"] = entry
            if f"t{sensor_id}" in existing_data:
                entry.insert(0, existing_data[f"t{sensor_id}"])

        save_button = tk.Button(calibration_window, text="Save Calibration", command=self.save_calibration_data)
        save_button.pack(pady=10)

# Utility and Cleanup
    def log_message(self, message):
        self.log.insert(tk.END, f"{message}\n")
        self.log.see(tk.END)

    def tsa_select(self):
        print(f"Selected TSA: {self.tsaSelect}")
        self.TSA, _ = self.load_thermistor_sensor_assembly(self.tsaSelect)
 
    def log_temperatures_to_csv(self, temperatures, ref_temperature=None):
        filename = f"Tkinter_GUI/TestData/temperature_data_TSA{self.tsaVar.get()}_{self.start_dt}.csv"
        # Adjust headers to account for each sensor having dedicated columns for raw and calibrated temperatures
        headers = ["Timestamp", "Calibration On", "Ref Temperature"]
        for i in range(1, 7):
            headers.extend([f"Raw T{i}", f"Calibrated T{i}", f"Polynomial Coeffs T{i}"])

        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(headers)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cal_on = "Yes" if self.calOnVar.get() else "No"
            ref_temp_entry = ref_temperature if ref_temperature is not None else "N/A"

            # Prepare a list to accumulate data for all sensors
            sensor_data = []
            for sensor_id in range(1, 7):
                sensor_key = f"t{sensor_id}"
                raw_temp = temperatures[sensor_id - 1]
                calibrated_temp = "N/A"  # Default if calibration is off
                polynomial_coeffs = "N/A"
                if self.calOnVar.get():
                    calibrated_temp = self.TSA.get_calibrated_temp(sensor_key, raw_temp)
                    calibration_data = self.TSA.get_sensor_calibration(sensor_key)
                    polynomial_coeffs = ', '.join(map(str, calibration_data)) if calibration_data else "N/A"
                
                # Add sensor's raw temp, calibrated temp, and coeffs to the list
                sensor_data.extend([raw_temp, calibrated_temp, polynomial_coeffs])

            # Construct the row for this instance of logging
            row = [now, cal_on, ref_temp_entry] + sensor_data
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

if __name__ == "__main__":
    app = GUI("On-Instrument Slide Temperature Measurement System")
    app.window.mainloop()
