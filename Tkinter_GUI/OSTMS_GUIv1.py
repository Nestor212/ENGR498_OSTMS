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
# Placeholder for the serial port import
import serial
# Placeholder for listing serial ports
from serial.tools import list_ports

# Assuming you have an icon at the specified path
ICON_PATH = os.path.join(os.path.dirname(__file__), "icon.png")

class GUI:
    def __init__(self, title):
        
        self.isStarted = False
        now = datetime.now()
        self.start_dt = now.strftime("%Y_%m_%d_%H:%M")
        self.timer = 0
        
        self.window = tk.Tk()
        self.window.title(title)
        if ICON_PATH:
            self.window.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
        
        self.portNamesList = []
        self.baudRatesList = [
            1200,
            2400,
            4800,
            9600,
            19200,
            38400,
            57600,
            115200,
            230400,
            460800,
            576000,
            921600,
        ]
        
        self.guiUpdateInterval = 1000
        self.serialPortBaud = 9600
        self.serialPortManager = SerialPortManager(self.serialPortBaud)
        self.get_available_serial_ports()

        self.create_widgets()
        
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        
        # Temporary setup for demonstration purposes
        self.points = np.array([(0.5, 0.75), (2.5, 0.75), (1.15, 0.5), (1.85, 0.5), (0.5, 0.25), (2.5, 0.25)])
        self.temperatures = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Initial temperatures
        
        # Start the update process
        self.updateTemperaturePlot(True)

    def create_widgets(self):
        # Top frame for controls
        self.topFrame = tk.Frame(self.window)
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
        
        # Baud Label
        self.scanButton = tk.Label(self.topFrame, text="Baud Rate")
        self.scanButton.pack(side=tk.LEFT, padx=5, pady=20)
        
        # Baud rate selection dropdown
        self.baudVar = tk.StringVar(self.window)
        self.baudDropdown = ttk.Combobox(self.topFrame, textvariable=self.baudVar, values=self.baudRatesList, state='disabled')  # Example values
        self.baudDropdown.set(self.baudRatesList[3])
        self.baudDropdown.pack(side=tk.LEFT, padx=5, pady=20)
        
        # Connect button
        self.connectButton = tk.Button(self.topFrame, text="Connect", command=self.connect, state='disabled')
        self.connectButton.pack(side=tk.LEFT, padx=20, pady=20)
        
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

    def scan_ports(self):
        # Placeholder function to scan serial ports
        self.log.insert(tk.END, "Scanning ports...\n")
        self.portNamesList = self.get_available_serial_ports()

        if len(self.portNamesList) == 0:
            self.isAnyPortAvailable = False
            self.portNamesList = ["No ports available"]
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
                
        self.update_option_menu(self.portNamesList)

    def update_option_menu(self, portNames):
        # Remove old items
        self.portDropdown.delete(0, "end")
        # Set default value of selectedPort
        self.portDropdown['values'] = portNames
        self.selectedPort.set(portNames[0])
        
    def connect(self):
        # Function to handle connection
        if self.isStarted == False:
            self.log.insert(tk.END, "Connecting...\n")
            self.isStarted = True
            self.connectButton.configure(text="Disconnect")
            # Get desired serial port name
            self.serialPortName = self.selectedPort.get()
            # Get desired serial port baud rate
            self.serialPortBaud = self.baudVar.get()
            # Start Serial Port Communication
            self.serialPortManager.set_name(self.serialPortName)
            self.serialPortManager.set_baud(self.serialPortBaud)
            self.serialPortManager.start()
            # Start updating textbox in GUI
            self.log.insert(tk.END, "Connected to: " + self.serialPortName + "\n")
            self.recursive_update_textbox(True)
        else:
            self.isStarted = False
            self.connectButton.configure(text="Connect")
            self.serialPortManager.stop()
            self.log.insert(tk.END, "Disconnected.\n")
        
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
        self.temperatures += np.random.randn(*self.temperatures.shape) * 0.1
        
        rbf = Rbf(self.points[:, 0], self.points[:, 1], self.temperatures, function='multiquadric', smooth=0)
        grid_x, grid_y = np.mgrid[0:3:100j, 0:1:100j]
        grid_z = rbf(grid_x, grid_y)
        
        self.ax.clear()
        im = self.ax.imshow(grid_z.T, extent=(0,3,0,1), origin='lower', cmap='coolwarm', vmin=0, vmax=100)
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
                
            with open('TestData/Test_' + self.start_dt + ".csv", 'a', newline='\n' ) as file:
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
    


class SerialPortManager:
    # A class for management of serial port data in a separate thread
    def __init__(self, serialPortBaud=9600):
        self.now = datetime.now()
        self.isRunning = False
        self.serialPortName = None
        self.serialPortBaud = serialPortBaud
        self.serialPort = serial.Serial()
        self.serialPortBuffer = ""

    def set_name(self, serialPortName):
        self.serialPortName = serialPortName

    def set_baud(self, serialPortBaud):
        self.serialPortBaud = serialPortBaud

    def start(self):
        self.isRunning = True
        self.serialPortThread = threading.Thread(target=self.thread_handler)
        self.serialPortThread.start()

    def stop(self):
        self.isRunning = False

    def thread_handler(self):

        while self.isRunning:
            if not self.serialPort.isOpen():
                self.serialPort = serial.Serial(
                    port=self.serialPortName,
                    baudrate=self.serialPortBaud,
                    bytesize=8,
                    timeout=2,
                    stopbits=serial.STOPBITS_ONE,
                )
            else:
                # Wait until there is data waiting in the serial buffer
                for i in range(6):
                    # Read only one byte from serial port
                    self.serialPortBuffer = self.serialPort.readline().decode("utf-8")
                    # Process incoming bytes
                    self.main_process(self.serialPortBuffer)

        if self.serialPort.isOpen():
            self.serialPort.close()



    def read_buffer(self):
        # Return a copy of serial port buffer
        return self.serialPortBuffer

    def __del__(self):
        if self.serialPort.isOpen():
            self.serialPort.close()

    def main_process(self, inputBytes):
        # Print the received byte in Python terminal
        try:
            data = inputBytes
        except UnicodeDecodeError:
            pass
        else:
            pass
            #print(data, end="")

if __name__ == "__main__":
    app = GUI("On-Instrument Slide Teamperature Measurement System")
    app.window.mainloop()
