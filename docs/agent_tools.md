# Agent tools for local model

## retrieve_laws(question,top_k) -> List[chunk]

### Description

This tool searchs and extracts relevant paragraphs (chunks) related to a specific question from database.

### Input
class RetrieveInput:
    question: str
    top_k: int

### Output
class RetrieveOutput:
    chunks: List[chunk]

## generate_answer(question,chunks) -> str

### Description

This tool generates the answer, with LLM from the user question and relevant chunks from output of retrieve_laws

### Input
class GenerateInput:
    question: str
    chunks: List[chunk]

### Output
class GenerateOutput:
    answer: str

## format_citation(answer,chunks) -> str

### Description

This tool reformats the answer and add more citations from all laws used. It helps people check the information origin and increase trust.

### Input
class FormatInput:
    answer: str
    chunks: List[chunk]

### Output
class FormatOutput:
    formatted_answer: str
