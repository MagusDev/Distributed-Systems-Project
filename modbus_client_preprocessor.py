import time
import json
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

class ModbusClient:
    def __init__(self, host='localhost', port=5020):
        self.host = host
        self.port = port
        self.client = ModbusTcpClient(host, port)

    def connect(self):
        """Connect to the Modbus server."""
        if not self.client.connect():
            print(f"Failed to connect to Modbus server at {self.host}:{self.port}")
            return False
        print(f"Connected to Modbus server at {self.host}:{self.port}")
        return True

    def read_plc_data(self):
        """Read PLC data from the Modbus server."""
        try:
            # Read holding registers (address 0, count 4)
            response = self.client.read_holding_registers(address=0, count=4, unit=1)
            if response.isError():
                print(f"Error reading Modbus registers: {response}")
                return None

            # Decode the response (assuming the data is stored as 32-bit floats)
            decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            motor_speed = decoder.decode_32bit_float()
            power_output = decoder.decode_32bit_float()
            system_pressure = decoder.decode_32bit_float()
            oil_temperature = decoder.decode_32bit_float()

            # Create a dictionary with the decoded data
            plc_data = {
                'motor_speed': motor_speed,
                'power_output': power_output,
                'system_pressure': system_pressure,
                'oil_temperature': oil_temperature
            }
            return plc_data

        except Exception as e:
            print(f"Error reading PLC data: {e}")
            return None

    def preprocess_data(self, plc_data):
        """Preprocess the PLC data (e.g., scaling, filtering, etc.)."""
        if not plc_data:
            return None

        # Example preprocessing: Convert motor speed from RPM to rad/s
        plc_data['motor_speed_rads'] = plc_data['motor_speed'] * 0.10472

        # Example preprocessing: Convert power output from kW to MW
        plc_data['power_output_mw'] = plc_data['power_output'] / 1000.0

        # Example preprocessing: Add a timestamp
        plc_data['timestamp'] = time.time()

        return plc_data

    def run(self):
        """Run the Modbus client and preprocess data."""
        if not self.connect():
            return

        while True:
            try:
                # Read data from the Modbus server
                plc_data = self.read_plc_data()

                # Preprocess the data
                preprocessed_data = self.preprocess_data(plc_data)

                # Log the preprocessed data
                if preprocessed_data:
                    print(f"Preprocessed PLC data: {json.dumps(preprocessed_data, indent=2)}")

                # Wait before the next read
                time.sleep(1)

            except Exception as e:
                print(f"Error in Modbus client: {e}")
                time.sleep(1)

if __name__ == "__main__":
    modbus_client = ModbusClient(host='localhost', port=5020)
    modbus_client.run()
    