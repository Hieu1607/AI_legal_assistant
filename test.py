from datetime import datetime


def add(x, y):
    return x + y


def print_result():
    now = datetime.now()
    print("Hello, result is", add(5, 7), "at", now)


print_result()
