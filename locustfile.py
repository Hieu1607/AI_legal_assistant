import random
import threading

import pandas as pd
from locust import HttpUser, constant, task
from locust.env import Environment

df = pd.read_excel("Bộ câu hỏi pháp luật.xlsx")
questions = df["Nội dung"].tolist()


class GlobalCounter:
    def __init__(self):
        self.rag_count = 0
        self.lock = threading.Lock()
        self.MAX_REQUESTS = 30

    def increment_and_check(self):
        with self.lock:
            if self.rag_count >= self.MAX_REQUESTS:
                return False
            self.rag_count += 1
            print(f"Total RAG requests: {self.rag_count}/{self.MAX_REQUESTS}")
            return True


global_counter = GlobalCounter()


class MyUserBehavior(HttpUser):
    host = "https://ai-legal-assistant-8g4g.onrender.com"
    wait_time = constant(1)  # Minimal wait time

    connection_timeout = 20
    network_timeout = 120

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_asked = False
        self.my_question = random.choice(
            questions
        )  # Each user gets one random question

    @task
    def post_rag(self):
        # Each user only asks one question
        if self.has_asked:
            return

        # Check if we've reached the limit
        if not global_counter.increment_and_check():
            return

        self.has_asked = True
        print(f"User asking: {self.my_question[:50]}...")

        # Ask the RAG question
        response = self.client.post(
            "/rag",
            json={"question": self.my_question},
            timeout=(self.connection_timeout, self.network_timeout),
        )

        print(f"Response status: {response.status_code}")

        # Check if we've reached 30 requests, then stop the test
        with global_counter.lock:
            if global_counter.rag_count >= 30:
                print("Reached 30 requests. Stopping test...")
                self.environment.runner.stop()
                return


# Usage: locust -f locustfile.py --users=30 --spawn-rate=0.5 --run-time=300s
# This will create 30 users over 60 seconds (0.5 users/second), each asking one random RAG question
# All 30 requests will be spread across 1 minute, then stop automatically
