# -*- coding: utf-8 -*-
from locust import HttpUser, between, task


class MyWebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task  # type: ignore
    def visit_homepage(self):
        self.client.get("/")

    @task  # type: ignore
    def visit_retrieve(self):
        self.client.post(
            "/retrieve",
            json={"question": "Chương II điều 29 bộ luật hình sự", "top_k": 5},
        )
