# Schema for all chunks containers

## A law_id.json schema will consist of:
- title(String)
- chunk_id(Int)
- chapter_title(String)
- section_title(Int)
- date_of_issue(dd/mm/yyyy)
- update_day(dd/mm/yyyy)
- content(String)

## A rule_id.json schema will be:
- title(String)
- chunk_id(Int)
- chapter_title(String)
- section_title(Int)

## Folder structure
```
AI_legal_assistant/
├── data/
│   └── raw/
│   └── processed/
│       └── laws/
│           └── law_id.json/
│       └── rules/
│           └── chu_de_.../
│       └── processed_rules/
│           └── chu_de/
│               └── de_muc/
│                   └── rule_id.json/
```
