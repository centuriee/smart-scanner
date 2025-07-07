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
    year_processed: str
    funding: Optional[str] = None

class Document(BaseModel):
    classification: Classification
    metadata: Optional[Metadata] = None

def analyzeDocument(doc, filename) -> Document:

    # classification prompt
    classifyPrompt = f'''{doc}

    QUERY: You are tasked with identifying the subject, classification type, year processed, and funding (if applicable) from the given document with filename {filename}.

    Instructions:  

    Subject. The subject is usually found at the beginning of the document. If the subject is not clearly stated in the content, use the full filename  as the subject. Make sure to match the capitalization and formatting of the filename exactly. Example: If the filename is Letter of Appreciation_Webinar_ Ms. Narag_30 Sept 2024.md, then the subject should be: Letter of Appreciation_Webinar_ Ms. Narag_30 Sept 2024
             
    Year Processed. Look for a date mentioned at the start of the document. Extract the year from that date. Example: If the date is October 1, 2024, the year processed is 2024.
        
    Classification Type. Classify the document using one of these seven categories:
        ACA : Academic
        ADM : Administration and Management
        CRE : Creative Work, Research, and Extension
        FIN : Financial
        LEG : Legal
        PER : Personnel
        SAS : Student Affairs and Services
             
        If the document is classified as CRE, determine the funding source: INT (internally funded), or EXT (externally funded). If the document is not CRE, the funding field must be set to null. For the type and funding, simply write the three letter code.
         
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