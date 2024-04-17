"""
Title: On-Instrument Slide Temperature Measurement System GUI
Version: 1.1
Author: Nestor Garcia
Date: 01 Mar 24
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
- Improved error handling and conditional behaviour throughout.

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
        self.baudRatesList = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 576000, 921600]
        
        self.guiUpdateInterval = 1000
        self.serialPortBaud = 9600
        self.serialPortManager = SerialPortManager(self.serialPortBaud)
        self.get_available_serial_ports()

        self.create_widgets()
        
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.points = np.array([(1.125, 0.75), (2.625, 0.75), (1.5750, 0.5), (2.125, 0.5), (1.125, 0.25), (2.625, 0.25)])
        #self.points = np.array([(0.5, 0.75), (2.5, 0.75), (1.15, 0.5), (1.85, 0.5), (0.5, 0.25), (2.5, 0.25)])
        self.temperatures = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
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
        
        # Baud Label
        self.scanButton = tk.Label(self.topFrame, text="Baud Rate")
        self.scanButton.pack(side=tk.LEFT, padx=5, pady=20)
        
        # Baud rate selection dropdown
        self.baudVar = tk.StringVar(self.window)
        self.baudDropdown = ttk.Combobox(self.topFrame, textvariable=self.baudVar, values=self.baudRatesList, state='disabled')  # Example values
        self.baudDropdown.set(self.baudRatesList[3])
        self.baudDropdown.pack(side=tk.LEFT, padx=5, pady=20)
        self.baudDropdown.bind('<<ComboboxSelected>>', self.on_combobox_select)
        
        # LED indicator as a canvas, updated to draw a circle
        self.ledIndicator = tk.Canvas(self.topFrame, width=20, height=20, bg="#303030", highlightthickness=0)  # Background as white or any neutral color
        self.ledCircle = self.ledIndicator.create_oval(2, 2, 18, 18, fill="red")  # Start as red (disconnected)
        self.ledIndicator.pack(side=tk.LEFT, padx=(50, 0), pady=20)
        
        # Connect button
        self.connectButton = tk.Button(self.topFrame, text="Connect", command=self.connect, state='disabled')
        self.connectButton.pack(side=tk.LEFT, padx=(10, 40), pady=20)
        
        self.temp = [tk.Label()] * 6
        self.thermistor = [tk.Label()] * 6
        self.temperatureDataBox = tk.LabelFrame(self.window, text="Temperatures",labelanchor ='n', font=("Helvetica", 18, 'bold'), fg = "#000000", bd = 0, bg="#ffffff", height = 200, width=self.window.winfo_width())
        self.temperatureDataBox.pack(side=tk.TOP, fill = tk.X)        
        
        self.thermistor[0] = tk.Label(self.temperatureDataBox, text="T1", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[0].place(x = 200, y = 10)
        self.temp[0] = tk.Label(self.temperatureDataBox, text="0.00°C", bg="#ffffff", fg = "#000000")
        self.temp[0].place(x = 200-8, y = 10+20)
        
        self.thermistor[1] = tk.Label(self.temperatureDataBox, text="T2", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[1].place(x = 610, y = 10)
        self.temp[1] = tk.Label(self.temperatureDataBox, text="00.0°C", bg="#ffffff", fg = "#000000")
        self.temp[1].place(x = 610-8, y = 10+20)
        
        self.thermistor[2] = tk.Label(self.temperatureDataBox, text="T3", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[2].place(x = 330, y = 60)
        self.temp[2] = tk.Label(self.temperatureDataBox, text="0.00°C", bg="#ffffff", fg = "#000000")
        self.temp[2].place(x = 330-8, y = 60+20)     
        
        self.thermistor[3] = tk.Label(self.temperatureDataBox, text="T4", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[3].place(x = 480, y = 60)
        self.temp[3] = tk.Label(self.temperatureDataBox, text="0.00°C", bg="#ffffff", fg = "#000000")
        self.temp[3].place(x = 480-8, y = 60+20)
        
        self.thermistor[4] = tk.Label(self.temperatureDataBox, text="T5", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[4].place(x = 200, y = 110)
        self.temp[4] = tk.Label(self.temperatureDataBox, text="0.00°C", bg="#ffffff", fg = "#000000")
        self.temp[4].place(x = 200-8, y = 110+20)
        
        self.thermistor[5] = tk.Label(self.temperatureDataBox, text="T6", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.thermistor[5].place(x = 610, y = 110)
        self.temp[5] = tk.Label(self.temperatureDataBox, text="0.00°C", bg="#ffffff", fg = "#000000")
        self.temp[5].place(x = 610-8, y = 110+20)
        
        self.refLabel = tk.Label(self.temperatureDataBox, text="Ref:  ", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.refLabel.place(x = 750, y = 60)
        self.refTempLabel = tk.Label(self.temperatureDataBox, text="N/A", bg="#ffffff", fg = "#000000")
        self.refTempLabel.place(x = 750+40, y = 60)
        
        self.datetimeLabel = tk.Label(self.temperatureDataBox, text="Datetime: ", font=("Helvetica", 16, 'bold'), bg="#ffffff", fg = "#000000")
        self.datetimeLabel.place(x = 320, y = 155)
        self.datetimeData = tk.Label(self.temperatureDataBox, text="0.00", bg="#ffffff", fg = "#000000")
        self.datetimeData.place(x = 320+80, y = 155)
        
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
            self.baudDropdown.configure(state="disabled")
            self.connectButton.configure(state="disabled")
        else:
            self.isAnyPortAvailable = True
            self.portDropdown.configure(state="normal")
            self.baudDropdown.configure(state="normal")
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
            
    def connect(self):
        if not self.isStarted:
            self.log.insert(tk.END, "Connecting...\n")
            self.isStarted = True
            self.connectButton.configure(text="Disconnect")
            self.serialPortName = self.selectedPort.get()
            self.serialPortBaud = int(self.baudVar.get())
            try:
                self.serialPortManager.stop()  # Ensure previous connection is properly closed
                self.serialPortManager.set_name(self.serialPortName)
                self.serialPortManager.set_baud(self.serialPortBaud)
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
            self.connectButton.configure(text="Connect")
            self.serialPortManager.stop()
            self.log.insert(tk.END, "Disconnected.\n")
            self.ledIndicator.itemconfig(self.ledCircle, fill="red")  # Change LED to red

    def updateTemperatures(self):
        thermtokens1 = self.buffer.rstrip().split(" | ")
        
        for i in thermtokens1:
            thermTokens = i.split(" ")
        
            if thermTokens[0] == 'T1':
                self.temp[0].configure(text = (thermTokens[1]) + "°C")
                self.temperatures[0] = float(thermTokens[1])
            elif thermTokens[0] == 'T2':
                self.temp[1].configure(text = (thermTokens[1]) + "°C")
                self.temperatures[1] = float(thermTokens[1])
            elif thermTokens[0] == 'T3':
                self.temp[2].configure(text = (thermTokens[1]) + "°C")
                self.temperatures[2] = float(thermTokens[1])
            elif thermTokens[0] == 'T4':
                self.temp[3].configure(text = (thermTokens[1]) + "°C")
                self.temperatures[3] = float(thermTokens[1])
            elif thermTokens[0] == 'T5':
                self.temp[4].configure(text = (thermTokens[1]) + "°C") 
                self.temperatures[4] = float(thermTokens[1])      
            elif thermTokens[0] == 'T6':
                self.temp[5].configure(text = (thermTokens[1]) + "°C")    
                self.temperatures[5] = float(thermTokens[1])
            elif thermTokens[0] == 'Ref':
                self.refTempLabel.configure(text = (thermTokens[1]) + "°C")
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
                
            with open('Test_' + self.start_dt + ".csv", 'a', newline='\n' ) as file:
                writer = csv.writer(file,quoting=csv.QUOTE_MINIMAL)
                writer.writerow([dt_string + self.buffer.strip()])
            # for i in range(1):#7):
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

    def set_baud(self, serialPortBaud):
        self.serialPortBaud = serialPortBaud
            
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
          
if __name__ == "__main__":
    app = GUI("On-Instrument Slide Temperature Measurement System")
    app.window.mainloop()
