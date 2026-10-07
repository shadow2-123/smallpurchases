from pathlib import Path

from documents.parser import DocumentParser


SAMPLES_DIR = Path("samples")

parser = DocumentParser()

for path in sorted(SAMPLES_DIR.iterdir()):
    if path.suffix.lower() not in {".doc", ".docx"}:
        continue

    document = parser._read(
        data=path.read_bytes(),
        format_=path.suffix.lower().lstrip("."),
    )

    delivery_term = parser._find_delivery_term(document)

    print("=" * 80)
    print(path.name)
    print(f"DELIVERY: {delivery_term}")
    print()