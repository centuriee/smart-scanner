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
    funding: Optional[str] = None

class Document(BaseModel):
    classification: Classification
    metadata: Optional[Metadata] = None

def analyzeDocument(doc, filename) -> Document:

    # classification prompt
    classifyPrompt = f'''{doc}

    QUERY: You are a model tasked to decipher and identify the complete subject and classification of the inputted document. There are 7 ways to classify a document: 

    - ACA (academic)
    - ADM (administration and management)
    - CRE (creative work, research and extension)
        - under CRE, there are two funding types: INT (internally) and EXT (externally). if the document is not CRE, funding must be NULL.
    - FIN (financial)
    - LEG (legal)
    - PER (personnel)
    - SAS (student affairs and services)

    The subject is usually indicated near the start of the document. However, if it is difficult to determine the subject from the content, you must use the full filename of the document as the subject: {filename}. Ensure that the capitalization matches the filename exactly.

    For the type and funding of the application, simply write the three letter code.
    
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

    if classification.funding == "null" or classification.type.upper() != "CRE":
        classification.funding = None

    # metadata prompt, ignore if not CRE
    metadata = None
    if classification.type.upper() == "CRE":
        metadataPrompt = f'''{doc}

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

        For instances wherein a field is not stated within the document, leave it as null.

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

        for field, value in metadata.model_dump().items():
            if isinstance(value, str) and value.strip().lower() == "null":
                setattr(metadata, field, None)

    return Document(classification = classification, metadata = metadata)