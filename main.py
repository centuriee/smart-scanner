from scripts.documentParser import parseDocument
from scripts.fileFunctions import getFilename, getSource, writeToMarkdown, writeToJSON
from scripts.aiFunctions import analyzeDocument


# PDF PARSING SECTION
source = getSource("testDocuments/") # pass parent directory
doc = parseDocument(source)
mdFilename = getFilename(source, 2)
writeToMarkdown(doc, mdFilename)

# ANALYSIS SECTION
documentMetadata = analyzeDocument(doc)
jsonFilename = getFilename(source, 1)
writeToJSON(documentMetadata, jsonFilename)