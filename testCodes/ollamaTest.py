import os
import json
from ollama import chat
from pydantic import BaseModel

# source can be local path or URL
source = input("Enter MD name with extension: ")

with open(source, "r", encoding="utf-8") as file:
    doc = file.read()

# JSON metadata format
class Metadata(BaseModel):
    title: str
    authors: list[str]
    presenting_author: str
    conference: str
    conference_date: str
    location: str
    abstract: str
    keywords: list[str]

# constructing prompt
prompt = f'''{doc}
\n\n
QUERY: You are a parsing assistant tasked to extract the following fields from the inputted research paper in READme format and return them strictly in JSON format:
{{
    "title": "...",
    "authors": [...],
    "presenting_author": "...",
    "conference": "...",
    "conference_date": "...",
    "location": "...",
    "abstract": "...",
    "keywords": [...]
}}
To help in finding the study's title, it is usually stylized as a ## MARKDOWN HEADING, with the other fields such as authors, abstract and keywords directly following it. The abstract usually starts with "Abstract: " while the keywords start with "Keywords: ".
\n\n
/nothink /no_think
'''

# PASS PROMPT
stream = chat(
    model = 'qwen3',
    messages = [
        {
            'role': 'user',
            'content': prompt
        }
    ],
    stream = False,
    format = Metadata.model_json_schema()
)

# PRINT MODEL OUTPUT
metadata = Metadata.model_validate_json(stream.message.content)
print(metadata)

# name for generated files based on pdf file name
filename = os.path.splitext(os.path.basename(source))[0]
jsonFilename = f"{filename}.json"

# write to json file
with open(jsonFilename, "w", encoding = "utf-8") as f:
    json.dump(metadata.model_dump(), f, ensure_ascii = False, indent = 4)

print(f"\nSaved JSON to {jsonFilename}") # success