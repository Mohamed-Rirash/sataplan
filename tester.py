from locust import HttpUser, task, between
import json

class SataplanUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    token = None

    def on_start(self):
        # Prepare authentication payload
        auth_data = {
            "grant_type": "password",
            "username": "Mohamed1",
            "password": "1234@1234Ma"
        }

        # Get authentication token first
        response = self.client.post("/auth/token",
                                    data=auth_data,  # Use data instead of json
                                    name="/auth/token")

        if response.status_code == 200:
            response_json = response.json()
            self.token = response_json.get("access_token")
            # Set default headers for all subsequent requests
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })
        else:
            print(f"Authentication failed: {response.text}")
            print(f"Response status code: {response.status_code}")

    @task(1)
    def index_page(self):
        self.client.get("/health")

    @task(2)
    def login(self):
        # Ensure we have a valid token
        if not self.token:
            self.on_start()

    @task(3)
    def get_goals(self):
        # Ensure we have a valid token before making the request
        if not self.token:
            self.on_start()

        # Correctly formatted goal payload
        goal_data = {
            "name": "Goal Test " + str(hash(self.token)),  # Unique goal name
            "description": "Locust Load Test Goal"
        }

        # Post goal with pre-set authentication headers
        self.client.post("/goals/add",
                         json=goal_data,
                         name="/goals/add")
