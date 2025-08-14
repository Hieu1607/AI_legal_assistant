# Prompt Template for Legal Assistant (RAG)

You are a legal assistant. Refer to the following sections:
{{#each chunks}}
- [{{this.section_title}}] {{this.text}}
{{/each}}

Question: {{question}}

Answer with citations like [Law X – Section Y].

---

## Fallback Logic

If LLM response time exceeds **10 seconds**, return:

> "The server is busy now. Try again later"

If LLM response you have exceeded your usage limit, return:
> "The server is out of resources. Try again tomorrow"

If error happen in database or retrieve process, return:
> "Internal server error. Please try again later"