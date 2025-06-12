import datetime
import json
import math
import os
import random as rnd
import sys
from typing import Dict, List


def my_complex_function(data_list: List[int], threshold: int = 10):
    """
    This function processes a list of integers based on a threshold.
    It's intentionally made a bit messy for testing.
    """
    processed_items = []
    # This line is intentionally very long to trigger Black's reformatting.
    # It also has inconsistent spacing.
    if len(data_list) > 0 and sum(data_list) / len(data_list) > 5:
        for item in data_list:
            if item > threshold:
                processed_items.append(
                    item * 2
                )  # Pylint might suggest using a comprehension
            else:
                processed_items.append(item + 1)
    else:
        print("No data or sum is too low.")
        # This print statement is not very useful and Pylint might flag it.
    return processed_items


class MyProcessor:
    def __init__(self, items):
        self.items = items

    def calculate_stats(self):
        # This method is missing a docstring, Pylint will complain.
        if not self.items:
            return 0, 0
        total = sum(self.items)
        average = total / len(self.items)
        return total, average


def main_execution_logic():
    """
    Main logic to test the functions.
    """
    print("--- Starting Tool Test ---")

    sample_data = [1, 8, 12, 4, 20, 7, 15]
    results = my_complex_function(sample_data, 10)
    print(f"Results from complex function: {results}")

    processor = MyProcessor(results)
    current_total, current_average = processor.calculate_stats()
    print(f"Total: {current_total}, Average: {current_average}")

    # Using a module alias, Isort should handle this.
    print(f"Random number: {rnd.randint(1, 100)}")

    # An intentionally useless variable to trigger Pylint's unused variable warning
    unused_variable = "I'm not used anywhere!"

    print("--- Test Finished ---")


if __name__ == "__main__":
    main_execution_logic()
    # Pylint might prefer direct call of main_execution_logic() instead of the if __name__ block being short
    # Or might complain about the empty line before if __name__.
    # Pylint might prefer direct call of main_execution_logic() instead of the if __name__ block being short
    # Or might complain about the empty line before if __name__.
