import os
import sys
from docling.document_converter import DocumentConverter
from ollama import chat

# source can be local path or URL
source = "testDocuments/" + input("Enter PDF name with extension (should be in testDocuments folder): ")

if os.path.exists(source):
    print("\n" + source + " exists. Converting file...\n")
else:
    print("\n" + source + " does not exist. Exiting program.\n")
    sys.exit(1)

# print("Source: " + source)
converter = DocumentConverter()
result = converter.convert(source)

# name for generated files based on pdf file name
# filename = os.path.splitext(os.path.basename(source))[0]
# jsonFilename = f"{filename}.json"
# mdFilename = f"{filename}.md"

"""
# JSON
resultDict = result.document.export_to_dict()

# write to json file
with open(jsonFilename, "w", encoding = "utf-8") as f:
    json.dump(resultDict, f, ensure_ascii = False, indent = 4)

print(f"\nSaved JSON to {jsonFilename}") # success
"""

# convert to markdown file
doc = result.document.export_to_markdown()

print("\nFile parsed. Extracting info...\n")


# define prompt
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
Only return the JSON object without additional text. To help in finding the study's title, it is usually stylized as a ## MARKDOWN HEADING, with the other fields such as authors, abstract and keywords directly following it. The abstract usually starts with "Abstract: " while the keywords start with "Keywords: ".
\n\n
/nothink /no_think
'''

# change this soon
stream = chat(
    model = 'qwen3',
    messages=[{'role': 'user', 'content': prompt}],
    stream = True,
)

for chunk in stream:
  print(chunk['message']['content'], end='', flush = True)