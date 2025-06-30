import os
from docling.document_converter import DocumentConverter

# source can be local path or URL
# docName = input("Enter PDF name with extension: ")

source = "testDocuments/Malaque III - Approve_Application.pdf"
# print("Source: " + source)
converter = DocumentConverter()
result = converter.convert(source)

# name for generated files based on pdf file name
filename = os.path.splitext(os.path.basename(source))[0]
jsonFilename = f"{filename}.json"
mdFilename = f"{filename}.md"

"""
# JSON
resultDict = result.document.export_to_dict()

# write to json file
with open(jsonFilename, "w", encoding = "utf-8") as f:
    json.dump(resultDict, f, ensure_ascii = False, indent = 4)

print(f"\nSaved JSON to {jsonFilename}") # success
"""

# MARKDOWN
doc = result.document.export_to_markdown()

# write to doc file
with open(mdFilename, "w", encoding = "utf-8") as f:
    f.write(doc)

print(f"\nSaved Markdown to {mdFilename}") # success