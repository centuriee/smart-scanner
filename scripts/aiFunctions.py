from ollama import chat
from pydantic import BaseModel
from typing import Optional

# classes for JSON structuring
class Metadata(BaseModel):
    title: str
    authors: list[str]
    presenting_author: str
    conference: str
    conference_date: str
    location: str
    abstract: str
    keywords: list[str]

class Classification(BaseModel):
    subject: str
    type: str

class Document(BaseModel):
    classification: Classification
    metadata: Optional[Metadata] = None

def analyzeDocument(doc) -> Document:

    # classification prompt
    classifyPrompt = f'''{doc}

    QUERY: You are a model tasked to decipher and identify the complete subject and classification of the inputted document. There are 7 ways to classify a document: 

    - ACA (academic)
    - ADM (administration and management)
    - CRE (creative work, research and extension)
    - FIN (financial)
    - LEG (legal)
    - PER (personnel)
    - SAS (student affairs and services)

    The subject is indicated near the start of the document, usually starting with "SUBJECT: ". After identifying the subject, ensure that its capitalization is consistent to the Markdown file.
    
    /nothink /no_think
    '''

    classifyResponse = chat(
        model = 'qwen3',
        messages = [
            {
                'role': 'user',
                'content': classifyPrompt
            }
        ],
        stream = False,
        format = Classification.model_json_schema()
    )

    classification = Classification.model_validate_json(classifyResponse.message.content)

    # metadata prompt, ignore if not CRE
    metadata = None
    if classification.type.upper() == "CRE":
        metadataPrompt = f'''{doc}
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
        metadataResponse = chat(
            model = 'qwen3',
            messages = [
                {
                    'role': 'user',
                    'content': metadataPrompt
                }
            ],
            stream = False,
            format = Metadata.model_json_schema()
        )

        metadata = Metadata.model_validate_json(metadataResponse.message.content)

    return Document(classification = classification, metadata = metadata)