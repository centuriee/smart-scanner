from ollama import chat

with open("MalaqueIIIApplication.md", "r", encoding="utf-8") as file:
    doc = file.read()

# define prompt
prompt = f'''{doc}
\n\n
QUERY: You are a parsing assistant tasked to extract the following fields from the inputted research paper in READme format and return them strictly in JSON format:
{{
    "title": "...",
    "authors": [...],
    "presenting_author": "...",
    "conference_date": "...",
    "location": "...",
    "abstract": "...",
    "keywords": [...]
}}
Only return the JSON object without additional text. To help in finding the study's title, it is usually stylized as a ## MARKDOWN HEADING, with the other fields such as authors, abstract and keywords directly following it. The abstract usually starts with "Abstract: " while the keywords start with "Keywords: ".
\n\n
/nothink /no_think
'''

# print(doc + prompt)


stream = chat(
    model = 'qwen3:32b',
    messages=[{'role': 'user', 'content': prompt}],
    stream = True,
)

for chunk in stream:
  print(chunk['message']['content'], end='', flush = True)