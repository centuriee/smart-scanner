# RESOURCE: https://docling-project.github.io/docling/examples/minimal/

from docling.document_converter import DocumentConverter

def parseDocument(filename):
    pageRange = (1, 5) # adjust if needed
    converter = DocumentConverter()
    result = converter.convert(filename, page_range = pageRange)

    # convert to markdown file
    doc = result.document.export_to_markdown()
    return doc
