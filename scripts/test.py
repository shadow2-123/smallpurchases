from pathlib import Path

from documents.parser import DocumentParser


SAMPLES_DIR = Path("samples")


def print_results(
    title: str,
    values: list[str],
) -> None:
    if not values:
        print(f"{title}: None")
        return

    for i, value in enumerate(values, 1):
        print(f"{title} {i}: {value}")


def main() -> None:
    parser = DocumentParser()

    files = sorted(
        path
        for path in SAMPLES_DIR.iterdir()
        if path.suffix.lower() in {".doc", ".docx"}
    )

    for path in files:
        print("=" * 100)
        print(path.name)

        try:
            document = parser._read(
                data=path.read_bytes(),
                format_=path.suffix.lower().lstrip("."),
            )

            delivery_terms = parser._find_delivery_terms(document)
            delivery_places = parser._find_delivery_places(document)

            print_results("TERM", delivery_terms)
            print_results("PLACE", delivery_places)

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

    print("=" * 100)
    print(f"Проверено файлов: {len(files)}")


if __name__ == "__main__":
    main()