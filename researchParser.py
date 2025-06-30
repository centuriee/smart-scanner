import os
import sys
from docling.document_converter import DocumentConverter
from ollama import chat

# PDF PARSER
# source can be local path or URL
source = "testDocuments/" + input("Enter PDF name with extension (should be in testDocuments folder): ")

if os.path.exists(source):
    print("\n" + source + " exists. Converting file...\n")
else:
    print("\n" + source + " does not exist. Exiting program.\n")
    sys.exit(1)

# page range for rs papers = 5, might adjust soon
pageRange = (1, 5)

# print("Source: " + source)
converter = DocumentConverter()
result = converter.convert(source, page_range = pageRange)

# GENERATE MARKDOWN FILE FOR CHECKING, COMMENT IF NOT NEEDED
# convert to markdown file
doc = result.document.export_to_markdown()

# filename for md file
filename = os.path.splitext(os.path.basename(source))[0]
mdFilename = f"{filename}.md"

# write to md file
with open(mdFilename, "w", encoding = "utf-8") as f:
    f.write(doc)

print(f"\nSaved Markdown to {mdFilename}") # success

# AI ANALYSIS
print("\nFile parsed. Extracting info...\n")

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
Only return the JSON object without additional text. To help in finding the study's title, it is usually stylized as a ## MARKDOWN HEADING, with the other fields such as authors, abstract and keywords directly following it. The abstract usually starts with "Abstract: " while the keywords start with "Keywords: ".
\n\n
/nothink /no_think
'''

# PASS PROMPT
# change soon
stream = chat(
    model = 'qwen3',
    messages=[{'role': 'user', 'content': prompt}],
    stream = True,
)

# PRINT MODEL OUTPUT
for chunk in stream:
  print(chunk['message']['content'], end='', flush = True)