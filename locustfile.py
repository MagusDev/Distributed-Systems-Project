from locust import HttpUser, TaskSet, task, between

class APIGatewayBehavior(TaskSet):
    @task(1)
    def get_plc_data(self):
        self.client.get("/plc/data")

    @task(2)
    def get_plc_variables(self):
        self.client.get("/plc/variables")

class WebsiteUser(HttpUser):
    tasks = {APIGatewayBehavior: 3}
    wait_time = between(1, 5)

if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py --host=http://128.214.253.212:30000")