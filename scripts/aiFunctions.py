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
    author: str
    type: str
    year_processed: str
    funding: Optional[str] = None

class Document(BaseModel):
    classification: Classification
    metadata: Optional[Metadata] = None

def analyzeDocument(doc, filename) -> Document:

    # classification prompt
    classifyPrompt = f'''{doc}

    QUERY: You are tasked with identifying the subject, classification type, author, year processed, and funding (if applicable) from the given document.

    Instructions:  

    Subject. The subject should be a very concise summary of the document's main purpose or content. If the subject is not clearly stated in the content, generate a concise and accurate summary based on the information provided. Avoid using the filename directly unless no other content is available to form a summary. Maintain proper capitalization and formatting where appropriate. Avoid using characters that cannot be used in a file name.

    Author of the Letter: Identify the author of the letter based on the content of the document. If the author is not explicitly mentioned in the signature block (e.g., 'Sincerely, [Name]'), search for any mention of names in the body of the text, especially those associated with academic credentials (e.g., PhD), roles (e.g., Professor), or research papers. Consider those names as a potential candidate for the author of the letter. If the author's full name is provided (e.g., "Gian Paolo Plariza Jr."), format the output as: Lastname Suffix (if applicable) INITIALS → Plariza Jr. GP. If only a title or role is provided (e.g., "Director") and no name is given, simply write Unknown.
             
    Year Processed. Extract the 'Year Processed' from the document by finding the first full date mentioned at the beginning of the text. This date will be in the format: [Day] [Month] [Year]. Extract only the year portion from this date. For example, if the date is '18 November 2024', then the Year Processed is '2024'. Do not extract years from other parts of the document unless no date is found at the top.
        
    Classification Type. Classify the document using one of these seven categories:
        ACA : Academic (Academic Calendar, Class Records, Class Schedules, Course Outlines, Grades, Honorific Scholars, Student Records)
        ADM : Administration and Management (Request for Travel, Equipment Usage, Room Usage, Research Load Credit (RLC), Admin Load Credit (ALC), Extension Load Credit (ELC), Research Proposals (not yet approve), International Publication Award (IPA) Applications, Letter Communications, Office Performance Commitment and Review (OPCR), Certifications)
        CRE : Creative Work, Research, and Extension (Approved Research Projects (with Approved MOA, LIB, etc), Financial Reports, Liquidation Reports for In-house grants and API, Progress Reports, Terminal Reports, Project Extension Requests, Line-Item Budget (LIB))
        FIN : Financial (Payment to suppliers, Purchase Order (PO), Budget Utilization, Salaries, Budget Proposals, Purchase Request (PR), Abstract of Price Quotations (APQ), Ledger, Requisition Issue Slip (RIS), Inspection and Acceptance Report (IAR), Inventory Custodian Slip (ICS), Property Acknowledgement Receipt (PAR))
        LEG : Legal (MOU, MOA, NDA/NDU, SALN, other legal documents needing of notarization)
        PER : Personnel (Personnel Accomplishment Reports, COS, IPCR, PES, DTR, Notice of Temporary Appointments, Additional Assignments)
        SAS : Student Affairs and Services (Student Assistant Files, Internships, etc)
             
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