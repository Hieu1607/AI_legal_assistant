import logging
import os
import time
from datetime import datetime

import pandas as pd
from locust import HttpUser, between, events, task

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables to store questions and results
questions_list = []
results_data = []
current_question_index = 0
completed_requests = 0
total_questions = 30


def load_questions_from_excel(file_path, limit=30):
    """
    Load questions and standard answers from Excel file
    """
    global questions_list
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Excel file columns: {df.columns.tolist()}")
        logger.info(f"Excel file shape: {df.shape}")

        # Get questions and standard answers
        questions_column = (
            df.columns[1] if len(df.columns) > 1 else df.columns[0]
        )  # 'Nội dung câu hỏi'
        answers_column = (
            df.columns[2] if len(df.columns) > 2 else None
        )  # 'Đáp án chuẩn'

        questions_raw = df[questions_column].dropna().tolist()[:limit]
        answers_raw = (
            df[answers_column].dropna().tolist()[:limit] if answers_column else []
        )

        # Convert all questions to string and pair with answers
        questions_list = []
        for i, q in enumerate(questions_raw):
            if isinstance(q, str) and q.strip():
                question = q.strip()
            elif not isinstance(q, str):
                question = str(q).strip()
                if not question or question == "nan":
                    continue
            else:
                continue

            # Get corresponding answer
            standard_answer = ""
            if i < len(answers_raw) and answers_raw[i] is not None:
                if isinstance(answers_raw[i], str):
                    standard_answer = answers_raw[i].strip()
                else:
                    standard_answer = str(answers_raw[i]).strip()
                    if standard_answer == "nan":
                        standard_answer = ""

            questions_list.append(
                {
                    "question": question,
                    "standard_answer": standard_answer,
                    "index": len(questions_list) + 1,
                }
            )

        logger.info(f"Loaded {len(questions_list)} valid questions from {file_path}")
        return questions_list
    except Exception as e:
        logger.error(f"Error loading questions from Excel: {e}")
        return []


class RAGUser(HttpUser):
    """
    Locust User class for RAG API testing - sequential question processing
    """

    wait_time = between(2, 3)  # Wait 2-3 seconds between requests
    host = "https://ai-legal-assistant-zswt.onrender.com"

    def on_start(self):
        """Called when a user starts"""
        # Load questions if not already loaded
        global questions_list, current_question_index
        if not questions_list:
            load_questions_from_excel("Questions.xlsx", limit=30)

        # Get the next question sequentially
        if questions_list and current_question_index < len(questions_list):
            self.question_data = questions_list[current_question_index]
            self.question = self.question_data["question"]
            self.standard_answer = self.question_data["standard_answer"]
            self.question_index = current_question_index + 1
            current_question_index += 1
            self.has_question = True
        else:
            # If all questions are used, this user won't do anything
            self.has_question = False

    @task
    def rag_request(self):
        """
        Send POST request to RAG API with assigned question
        """
        # Declare global variables at the start
        global results_data, completed_requests, total_questions

        if not hasattr(self, "has_question") or not self.has_question:
            # Check if all requests are completed and stop if needed
            if completed_requests >= total_questions:
                self.environment.runner.quit()
            return

        payload = {"question": self.question}
        headers = {"Content-Type": "application/json"}

        start_time = time.time()

        with self.client.post(
            "/rag", json=payload, headers=headers, timeout=45, catch_response=True
        ) as response:
            end_time = time.time()
            query_time = end_time - start_time

            # Store result data with only required columns
            result_data = {
                "question": self.question,
                "standard_answer": self.standard_answer,
                "total_time": round(
                    query_time, 2
                ),  # Use query_time as total_time initially
            }

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    rag_answer = response_data.get("data", {}).get("answer", "")
                    api_total_time = (
                        response_data.get("data", {})
                        .get("timing", {})
                        .get("total_time", 0)
                    )

                    # Use API total time if available, otherwise use our measured time
                    result_data.update(
                        {
                            "rag_answer": rag_answer,
                            "total_time": round(
                                api_total_time if api_total_time > 0 else query_time, 2
                            ),
                        }
                    )

                    response.success()  # pyright: ignore[reportAttributeAccessIssue]
                    logger.info(
                        f"Question {self.question_index}/30 - Success - Total time: {result_data['total_time']:.2f}s"
                    )

                except Exception as e:
                    result_data["rag_answer"] = f"JSON Parse Error: {str(e)}"
                    response.failure(  # pyright: ignore[reportAttributeAccessIssue]
                        f"JSON Parse Error: {str(e)}"
                    )  # pyright: ignore[reportAttributeAccessIssue]
            else:
                result_data["rag_answer"] = f"HTTP Error: {response.status_code}"
                response.failure(  # pyright: ignore[reportAttributeAccessIssue]
                    f"HTTP {response.status_code}"
                )  # pyright: ignore[reportAttributeAccessIssue]
                logger.error(
                    f"Question {self.question_index}/30 - HTTP {response.status_code}"
                )

            # Store result globally and update counters
            results_data.append(result_data)
            completed_requests += 1

            # Check if all questions are completed
            if completed_requests >= total_questions:
                logger.info(
                    f"All {total_questions} questions completed. Stopping test..."
                )
                self.environment.runner.quit()

            # Mark this user as done
            self.has_question = False

    @task(1)
    def check_completion(self):
        """
        Check if all requests are completed and stop the test
        """
        global completed_requests, total_questions
        if completed_requests >= total_questions:
            logger.info(
                f"Completion check: {completed_requests}/{total_questions} completed. Stopping..."
            )
            self.environment.runner.quit()


# Event handlers for Locust
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    logger.info("=== RAG Sequential Test Started ===")
    global results_data, current_question_index, completed_requests, total_questions
    results_data = []
    current_question_index = 0
    completed_requests = 0
    # Set total questions based on loaded questions
    if questions_list:
        total_questions = len(questions_list)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    logger.info("=== RAG Sequential Test Completed ===")
    save_results_to_excel_locust(results_data)


def save_results_to_excel_locust(results):
    """
    Save Locust results to Excel file
    """
    if not results:
        logger.warning("No results to save")
        return

    try:
        # Create DataFrame
        df = pd.DataFrame(results)

        # Sort by question number if available
        if "question_number" in df.columns:
            df = df.sort_values("question_number")

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"rag_sequential_results_{timestamp}.xlsx"

        # Keep only required columns and rename them
        df_filtered = df[
            ["question", "standard_answer", "rag_answer", "total_time"]
        ].copy()
        df_filtered.columns = [
            "Câu hỏi ban đầu",
            "Câu trả lời mẫu",
            "Câu trả lời từ RAG",
            "Thời gian chạy (giây)",
        ]

        df_filtered.to_excel(output_file, index=False, sheet_name="RAG Test Results")

        logger.info(f"Results saved to {output_file}")

        # Print summary
        total_requests = len(results)
        successful_requests = len(
            [
                r
                for r in results
                if "rag_answer" in r
                and not r["rag_answer"].startswith("HTTP Error")
                and not r["rag_answer"].startswith("JSON Parse Error")
            ]
        )
        avg_query_time = (
            sum([r.get("total_time", 0) for r in results]) / total_requests
            if total_requests > 0
            else 0
        )

        print(f"\n=== SEQUENTIAL TEST SUMMARY ===")
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {total_requests - successful_requests}")
        print(
            f"Success rate: {(successful_requests/total_requests*100):.1f}%"
            if total_requests > 0
            else "0%"
        )
        print(f"Average total time: {avg_query_time:.2f} seconds")
        print(f"Results saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error saving results to Excel: {e}")
        # Fallback to CSV
        try:
            csv_file = (
                f"rag_sequential_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df_filtered.to_csv(csv_file, index=False)  # type: ignore
            logger.info(f"Results saved to CSV: {csv_file}")
        except Exception as csv_e:
            logger.error(f"Error saving to CSV: {csv_e}")


# Main execution for standalone testing (non-Locust mode)
def main_standalone():
    """
    Main function to run standalone RAG testing (for development/testing)
    """
    print("=== RAG API Sequential Testing ===")
    print("Loading questions from Excel file...")

    # Load questions from Excel
    questions_file = "Questions.xlsx"
    questions = load_questions_from_excel(questions_file, limit=30)

    if not questions:
        print(f"No questions found in {questions_file}. Please check the file.")
        return

    print(f"Found {len(questions)} questions.")
    print("Use this command to run sequential test:")
    print(
        "locust -f quick_test.py --headless --users=30 --spawn-rate=2 --run-time=300s --host=https://ai-legal-assistant-zswt.onrender.com"
    )
    print("\nNote: Test will auto-stop when all questions are completed!")


if __name__ == "__main__":
    # Check if running with Locust
    import sys

    if "locust" in sys.modules or "LOCUST_ENVIRONMENT" in os.environ:
        # Running with Locust - do nothing, let Locust handle it
        pass
    else:
        # Running standalone
        main_standalone()

# locust -f quick_test.py --headless --users=30 --spawn-rate=2 --run-time=600s --host=https://ai-legal-assistant-zswt.onrender.com
