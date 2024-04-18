import serial

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