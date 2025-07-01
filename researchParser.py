import os
import sys
import json
from docling.document_converter import DocumentConverter
from ollama import chat
from pydantic import BaseModel


# PDF PARSER
# source can be local path or URL
source = "testDocuments/" + input("Enter PDF name with extension (should be in testDocuments folder): ")

if os.path.exists(source):
    print("\n" + source + " exists. Converting file...\n")
else:
    print("\n" + source + " does not exist. Exiting program.\n")
    sys.exit(1)

# filenames for output files
filename = os.path.splitext(os.path.basename(source))[0]
mdFilename = f"{filename}.md"
jsonFilename = f"{filename}.json"

# page range for rs papers = 5, might adjust soon
pageRange = (1, 5)

# print("Source: " + source)
converter = DocumentConverter()
result = converter.convert(source, page_range = pageRange)

# GENERATE MARKDOWN FILE FOR CHECKING, COMMENT IF NOT NEEDED
# convert to markdown file
doc = result.document.export_to_markdown()

# write to md file
with open(mdFilename, "w", encoding = "utf-8") as f:
    f.write(doc)

print(f"\nSaved Markdown to {mdFilename}") # success


# AI ANALYSIS
print("\nFile parsed. Extracting info...\n")

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

# PASS PROMPT TO AI
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
# print(metadata)

# WRITE TO JSON FILE
with open(jsonFilename, "w", encoding = "utf-8") as f:
    json.dump(metadata.model_dump(), f, ensure_ascii = False, indent = 4)

print(f"\nSaved JSON to {jsonFilename}") # success