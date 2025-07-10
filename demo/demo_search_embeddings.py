import os
import sys

root = os.getcwd()

sys.path.insert(0, str(root))

from src.store_vector.search_embeddings import search_relevant_embeddings

example_text = "Chương 2 điều 7 Bộ luật hình sự là gì ?"

relevant_embeddings = search_relevant_embeddings(example_text, 5)

if relevant_embeddings["documents"] is not None:
    for index, rule in enumerate(relevant_embeddings["documents"][0]):
        print(rule, "\n", relevant_embeddings["cosine_similarities"][0][index])
    # print(relevant_embeddings["documents"])
