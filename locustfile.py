import random
import threading

import pandas as pd
from locust import HttpUser, constant, task

df = pd.read_excel("Bộ câu hỏi pháp luật.xlsx")
questions = df["Nội dung"].tolist()


class GlobalCounter:
    def __init__(self):
        self.health_count = 0
        self.rag_count = 0
        self.retrieve_count = 0
        self.agent_count = 0
        self.lock = threading.Lock()
        self.MAX_REQUESTS = 15
    
    def increment_and_check(self, counter_name):
        with self.lock:
            current_count = getattr(self, f"{counter_name}_count")
            if current_count >= self.MAX_REQUESTS:
                return False
            setattr(self, f"{counter_name}_count", current_count + 1)
            new_count = current_count + 1
            print(f"Total {counter_name} requests: {new_count}/{self.MAX_REQUESTS}")
            return True 

global_counter = GlobalCounter()


class MyUserBehavior(HttpUser):
    host = "https://ai-legal-assistant-8g4g.onrender.com"
    wait_time = constant(5)  # Time between requests to reduce load

    connection_timeout = 20
    network_timeout = 120

    @task(1)
    def health_check(self):
        if not global_counter.increment_and_check("health"):
            return
        
        self.client.get("/health", timeout=(5, 120))

    @task(2)  
    def post_retrieve(self):
        if not global_counter.increment_and_check("retrieve"):
            return
        
        self.client.post(
            "/retrieve",
            json={"top_k": 5, "question": random.choice(questions)},
            timeout=(self.connection_timeout, self.network_timeout),
        )

    @task(1)
    def post_rag(self):
        if not global_counter.increment_and_check("rag"):
            return  
            
        # RAG often takes the longest due to response generation
        self.client.post(
            "/rag",
            json={"question": random.choice(questions)},
            timeout=(self.connection_timeout, self.network_timeout),
        )

    @task
    def post_agent(self):
        if not global_counter.increment_and_check("agent"):
            return
        self.client.post(
            "/agent",
            json={
                "question": random.choice(questions),
                "top_k": 5,
                "total_steps": random.randint(1, 3),
                "timeout_sec": 30,
            },
            timeout=(self.connection_timeout, self.network_timeout),
        )

# locust -f locustfile.py --users=10 --spawn-rate=2