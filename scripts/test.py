from pathlib import Path
import sys

from documents.parser import DocumentParser


path = Path(sys.argv[1])

parser = DocumentParser()
document = parser._read(
    data=path.read_bytes(),
    format_=path.suffix.lower().lstrip("."),
)

print("\n=== PARAGRAPHS ===")
for i, paragraph in enumerate(document.paragraphs):
    print(f"{i}: {paragraph}")

print("\n=== TABLES ===")
for table_index, table in enumerate(document.tables):
    print(f"\n--- TABLE {table_index} ---")

    for row_index, row in enumerate(table.rows):
        print(f"{row_index}: {row}")