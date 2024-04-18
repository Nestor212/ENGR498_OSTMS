class ThermistorSensor:
    def __init__(self, identifier):
        self.identifier = identifier
        # Initialize with a default polynomial that represents a linear function y = x
        # This means no calibration effect by default
        self.polynomial_coeffs = [1, 0]  # Represents y = x
    
    def set_calibration_data(self, polynomial_coeffs):
        if isinstance(polynomial_coeffs, int):
            polynomial_coeffs = [polynomial_coeffs]  # Convert single integer to list
        self.polynomial_coeffs = polynomial_coeffs
    
    def get_calibration_data(self):
        return self.polynomial_coeffs
    
    def get_calibrated_temp(self, rawTemp):
        # Calculate calibrated temperature using polynomial coefficients
        calibrated_temp = sum(coef * rawTemp ** power for power, coef in enumerate(reversed(self.polynomial_coeffs)))
        # print(self.polynomial_coeffs)
        return calibrated_temp
    
    def __repr__(self):
        return f"ThermistorSensor(ID: {self.identifier}, Calibration Coeffs: {self.polynomial_coeffs})"

        
class ThermistorSensorAssembly:
    def __init__(self, identifier):
        self.identifier = identifier
        # Assuming 6 sensors in each assembly
        self.sensors = {f"t{i+1}": ThermistorSensor(f"t{i+1}") for i in range(6)}

    def get_ID(self):
        return self.identifier
    
    def set_sensor_calibration(self, sensor_id, polynomial_coeffs):
        if sensor_id in self.sensors:
            self.sensors[sensor_id].set_calibration_data(polynomial_coeffs)
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
        calibration_coeffs = {sensor_id: sensor.get_calibration_data() for sensor_id, sensor in self.sensors.items()}
        return f"ThermistorSensorAssembly(ID: {self.identifier}, Sensors Calibration: {calibration_coeffs})"

