import random

import pandas as pd
from locust import HttpUser, constant, task

df = pd.read_excel("Bộ câu hỏi pháp luật.xlsx")
questions = df["Nội dung"].tolist()


class MyUserBehavior(HttpUser):
    host = "https://ai-legal-assistant-8g4g.onrender.com"
    wait_time = constant(5)  # Time between requests to reduce load

    connection_timeout = 10
    network_timeout = 60

    @task(1)
    def health_check(self):
        self.client.get("/health", timeout=(5, 30))

    # @task(2)
    # def post_retrieve(self):
    #     self.client.post(
    #         "/retrieve",
    #         json={"top_k": 5, "question": random.choice(questions)},
    #         timeout=(self.connection_timeout, self.network_timeout),
    #     )

    @task(1)
    def post_rag(self):
        # RAG often takes the longest due to response generation
        self.client.post(
            "/rag",
            json={"question": random.choice(questions)},
            timeout=(self.connection_timeout, self.network_timeout),
        )

    # @task
    # def post_agent(self):
    #     self.client.post(
    #         "/agent",
    #         json={
    #             "question": random.choice(questions),
    #             "top_k": 5,
    #             "total_steps": random.randint(1, 3),
    #             "timeout_sec": 30,
    #         },
    #     )
