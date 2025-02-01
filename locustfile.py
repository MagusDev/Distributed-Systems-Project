from locust import HttpUser, TaskSet, task, between

class APIGatewayBehavior(TaskSet):
    @task(1)
    def get_plc_data(self):
        self.client.get("/plc/data")

    @task(2)
    def get_plc_variables(self):
        self.client.get("/plc/variables")

class PreprocessorBehavior(TaskSet):
    @task(1)
    def simulate_preprocessor(self):
        # Simulate a message being processed by the preprocessor
        self.client.post("/process", json={
            "plc_id": "test_plc",
            "timestamp": 1738421438.0400372,
            "variables": {
                "motor_speed": {"value": 0.0, "unit": "RPM", "normalized": 0.0},
                "power_output": {"value": 260.08, "unit": "kW", "normalized": 0.52016},
                "system_pressure": {"value": 1.63, "unit": "Bar", "normalized": 0.16299999999999998},
                "oil_temperature": {"value": 95.0, "unit": "°C", "normalized": 1.0}
            }
        })

class AnomalyDetectorBehavior(TaskSet):
    @task(1)
    def simulate_anomaly_detection(self):
        # Simulate a message being processed by the anomaly detector
        self.client.post("/detect", json={
            "plc_id": "test_plc",
            "timestamp": 1738421438.0400372,
            "variables": {
                "motor_speed": {"value": 0.0, "unit": "RPM", "normalized": 0.0},
                "power_output": {"value": 260.08, "unit": "kW", "normalized": 0.52016},
                "system_pressure": {"value": 1.63, "unit": "Bar", "normalized": 0.16299999999999998},
                "oil_temperature": {"value": 95.0, "unit": "°C", "normalized": 1.0}
            }
        })

class WebsiteUser(HttpUser):
    tasks = {APIGatewayBehavior: 3, PreprocessorBehavior: 1, AnomalyDetectorBehavior: 1}
    wait_time = between(1, 5)

if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py --host=http://localhost:8000")