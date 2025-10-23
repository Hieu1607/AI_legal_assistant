# Import the RAG user class from quick_test.py
from quick_test import RAGUser, load_questions_from_excel

# Load questions when module is imported
load_questions_from_excel("Questions.xlsx", limit=30)

# This file serves as the main locustfile
# The RAGUser class is defined in quick_test.py