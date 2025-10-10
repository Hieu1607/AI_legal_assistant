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
    wait_time = constant(2)  # Wait between requests

    connection_timeout = 30
    network_timeout = 180  # Increased timeout for slow responses

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_asked = False
        self.my_question = random.choice(questions)

    @task
    def post_rag(self):
        # Check if we've reached the limit first
        if not global_counter.increment_and_check():
            print("Reached maximum requests, user stopping...")
            return

        # Each user only asks one question
        if self.has_asked:
            return

        self.has_asked = True
        print(f"User asking: {self.my_question[:50]}...")

        try:
            # Ask the RAG question
            response = self.client.post(
                "/rag",
                json={"question": self.my_question},
                timeout=(self.connection_timeout, self.network_timeout),
            )

            if response.status_code == 200:
                print(
                    f"✅ Response success: {response.status_code}, Time: {response.elapsed.total_seconds():.2f}s"
                )
            else:
                print(f"❌ Response failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Request failed with exception: {str(e)}")

        # Check if we've reached 30 requests, then stop the test
        with global_counter.lock:
            if global_counter.rag_count >= 30:
                print("🎉 Reached 30 requests. Stopping test...")
                self.environment.runner.stop()
                return


# Usage: locust -f locustfile.py --users=30 --spawn-rate=2 --run-time=300s
# This will create 30 users over 15 seconds (2 users/second), each asking one random RAG question
# Test will run until 30 requests are completed or timeout is reached
#
# Alternative headless mode:
# locust -f locustfile.py --users=30 --spawn-rate=2 --run-time=300s --headless --html=results.html
