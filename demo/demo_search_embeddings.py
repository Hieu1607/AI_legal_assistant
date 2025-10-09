import os
import sys

root = os.getcwd()

sys.path.insert(0, str(root))

from src.store_vector.weaviate_search import get_searcher

example_text = "Chương 2 điều 7 Bộ luật hình sự là gì ?"

# Use Weaviate Query Agent instead of separate search
searcher = get_searcher()
answer = searcher.ask_question(example_text)

print("Question:", example_text)
print("\nAnswer from Weaviate Query Agent:")
print(answer)

# Close connection
searcher.close()
