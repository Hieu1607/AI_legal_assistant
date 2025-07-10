import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-large")
model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-large")


def rerank(query, docs):
    scores = []
    for doc in docs:
        inputs = tokenizer(query, doc, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits
        scores.append(logits.item())
    return sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
