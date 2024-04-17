import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
from matplotlib.dates import DateFormatter  # Make sure this is at the beginning of your file
import numpy as np
import traceback


class CSVPlotterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real-time CSV Plotter")
        self.geometry("800x600")

        # Plotting is active or paused
        self.plotting_active = True

        # Attributes
        self.file_path = None
        self.data = pd.DataFrame()

        # Button to load CSV
        load_button = ttk.Button(self, text="Load CSV", command=self.load_csv)
        load_button.pack(pady=20)

        # Pause/Resume Button
        self.pause_button = ttk.Button(self, text="Pause", command=self.toggle_plotting)
        self.pause_button.pack(pady=20)

        # Frame for Plot
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.plot_widget = self.canvas.get_tk_widget()
        self.plot_widget.pack(fill=tk.BOTH, expand=True)

        # Navigation Toolbar (Zoom, Pan, etc.)
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Animation
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000)

    def load_csv(self):
        file_path_temp = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path_temp:
            self.file_path = file_path_temp
            self.data = pd.read_csv(self.file_path)  # Initial load of the data
            self.update_plot()

    def toggle_plotting(self):
        self.plotting_active = not self.plotting_active
        self.pause_button.config(text="Resume" if not self.plotting_active else "Pause")

    def update_plot(self, frame=None):
        if self.file_path and self.plotting_active:
            try:
                new_data = pd.read_csv(self.file_path, parse_dates=['Timestamp'])
                new_data['Calibration On'] = new_data['Calibration On'].map({'Yes': True, 'No': False})
                
                if not new_data.equals(self.data):
                    self.data = new_data
                    self.ax.clear()  # Clear the previous plot
                    
                    # Check the 'Calibration On' column to decide which data to plot
                    if self.data['Calibration On'].iloc[-1]:
                        temp_columns = [f'Calibrated T{i}' for i in range(1, 7)]
                    else:
                        temp_columns = [f'Raw T{i}' for i in range(1, 7)]

                    # Plot each temperature column as a new line on the plot
                    for col in temp_columns:
                        # Convert the series to NumPy arrays
                        x = self.data['Timestamp'].to_numpy()
                        y = self.data[col].to_numpy()
                        self.ax.plot(x, y, label=col)  # Add label for the legend
                    
                    # Display the legend
                    self.ax.legend()

                    # Formatting the plot
                    self.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))
                    self.ax.figure.autofmt_xdate()  # Auto-format the dates
                    
                    self.ax.set_title("Sensor Data Over Time")
                    self.ax.set_xlabel("Time")
                    self.ax.set_ylabel("Temperature")
                    self.canvas.draw()
            except Exception as e:
                print(f"Error reading the file: {e}")
                traceback.print_exc()

app = CSVPlotterApp()
app.mainloop()
