from docling.document_converter import DocumentConverter

def parseDocument(filename):
    # ADJUST ENDPOINT IF NEEDED
    pageRange = (1, 5)
    converter = DocumentConverter()
    result = converter.convert(filename, page_range = pageRange)

    # convert to markdown file
    doc = result.document.export_to_markdown()
    return doc
