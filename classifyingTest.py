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
QUERY: You are a model tasked to decipher and identify the subject of the inputted document. To help in finding the subject, it is indicated near the start of the document, usually starting with "SUBJECT: ".
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
    stream = True,
)

# PRINT MODEL OUTPUT
for chunk in stream:
  print(chunk['message']['content'], end='', flush = True)

