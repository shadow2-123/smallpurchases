from pathlib import Path


class ExcludeFilter:
    def __init__(self, path: Path, prefixes: tuple[str, ...] = ("26", "27")) -> None:
        self.path = path
        self.prefixes = prefixes
        self.words = self._load(path)

    @staticmethod
    def _load(path: Path) -> list[str]:
        if not path.exists():
            return []
        words = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line.lower())
        return words

    def reload(self) -> None:
        self.words = self._load(self.path)

    def is_electro(self, codes: str) -> bool:
        return any(
            code.strip().startswith(self.prefixes)
            for code in codes.split(",")
            if code.strip()
        )

    def is_excluded(self, name: str, spec: str, codes: str) -> bool:
        text = f"{name} {spec}".lower()
        if not any(word in text for word in self.words):
            return False
        return not self.is_electro(codes)