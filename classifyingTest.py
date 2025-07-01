from ollama import chat
from pydantic import BaseModel

# source can be local path or URL
source = input("Enter MD name with extension: ")

with open(source, "r", encoding="utf-8") as file:
    doc = file.read()

# JSON metadata format
class Classification(BaseModel):
    subject: str
    type: str

# constructing prompt
prompt = f'''{doc}
\n\n
QUERY: You are a model tasked to decipher and identify the complete subject and classification of the inputted document. There are 7 ways to classify a document: 

- ACA (academic)
- ADM (administration and management)
- CRE (creative work, research and extension)
- FIN (financial)
- LEG (legal)
- PER (personnel)
- SAS (student affairs and services)

The subject is indicated near the start of the document, usually starting with "SUBJECT: ". After identifying the subject, ensure that its capitalization is consistent to the Markdown file.
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
    format = Classification.model_json_schema()
)

# PRINT MODEL OUTPUT
classification = Classification.model_validate_json(stream.message.content)
print(classification)