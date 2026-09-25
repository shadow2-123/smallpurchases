import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from db import Database

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
EXCLUDE = ROOT / "exclude.txt"
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory=STATIC), name="static")

class ExcludeIn(BaseModel):
    words: list[str]


def tail(path: Path, lines: int) -> str:
    if not path.exists():
        return ""
    chunk = path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]
    chunk.reverse()
    return "\n".join(chunk)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/exclude")
def get_exclude():
    if not EXCLUDE.exists():
        return {"words": []}
    words = []
    for line in EXCLUDE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.append(line)
    return {"words": words}


@app.put("/api/exclude")
def put_exclude(payload: ExcludeIn):
    cleaned = []
    for word in payload.words:
        word = word.strip()
        if word:
            cleaned.append(word)
    EXCLUDE.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    return {"words": cleaned}


@app.get("/api/logs/{name}")
def get_logs(name: str, lines: int = Query(150, ge=1, le=1000)):
    if name not in ("parse", "notify"):
        raise HTTPException(400, "only parse or notify")
    return {"name": name, "text": tail(ROOT / f"{name}.log", lines)}


@app.post("/api/reset-ignored")
def reset_ignored():
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    Database(str(ROOT / settings["db_path"])).reset_ignored()
    return {"ok": True}