# OSTMS GUI and Firmware Integration

## Description
This repository contains both the GUI and firmware components of the OSTMS project. The GUI is built with Python and handles plotting, data visualization, and serial communication. The firmware, written in C++, interacts directly with ADS124S08 ADC hardware to perform data acquisition and processing, which is then visualized and managed through the GUI.

## Installation

### Software:
1. Clone the repository:
git clone https://github.com/Nestor212/ENGR498_OSTMS.git
2. Install required Python dependencies:
pip install tkinter pandas matplotlib numpy scipy serial sqlite3


### Firmware:
1. Open the `.cpp` and `.h` files with an Arduino IDE or compatible platform.
2. Ensure your development board is connected and proper libraries are installed.
3. Upload the firmware to your hardware.

## Usage

### GUI Application
To start the GUI application, ensure you have Python and all required dependencies installed. Navigate to the project directory in your terminal and run the following command:
python OSTMS_GUI2v3.py
This will launch the GUI, where you can interact with the visualization tools, configure settings, and manage data streams from connected devices.

### Firmware
Before uploading the firmware to your hardware, make sure the development board is connected to your computer. Open the `OSTMS_main.cpp`, `ADS124S08.cpp`, and `ADS124S08.h` files with an Arduino IDE or any compatible C++ platform that supports your hardware.

1. **Compile the Firmware**: In your IDE, compile the firmware to check for any errors and ensure compatibility with your board.
2. **Upload the Firmware**: Upload the compiled firmware to your hardware. This process will vary depending on the IDE and hardware being used, but typically involves selecting the correct board and port from the IDE menu and clicking the upload button.
3. **Running the Firmware**: Once uploaded, the firmware will automatically run every time the hardware is powered on or reset. It begins monitoring and processing data according to the defined functions and interacts with the GUI through serial communication.

## Interacting Between GUI and Firmware
Ensure that the serial port settings in the GUI match those configured for the hardware device. The GUI will display data received from the hardware and send commands or configurations back to it. This interaction enables real-time data processing and visualization, facilitating extensive monitoring and analysis capabilities.

## Features
- **Interactive Data Visualization**
- **Hardware Interaction via Serial Communication**
- **Real-time Data Acquisition and Processing**

## Dependencies
- **Software**: Python 3.x, libraries (tkinter, pandas, matplotlib, numpy, scipy, serial, sqlite3)
- **Firmware**: Arduino IDE, libraries (SPI, ArduinoJson)

## Contributing
Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License


