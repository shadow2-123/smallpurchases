import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import date
from functools import lru_cache

from fastapi import Path as ApiPath
from db import Database

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
EXCLUDE = ROOT / "exclude.txt"
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory=STATIC), name="static")

class ExcludeIn(BaseModel):
    words: list[str]

class CalendarDayIn(BaseModel):
    is_non_working: bool
    description: str | None = None


class CalendarMonthIn(BaseModel):
    is_ready: bool


@lru_cache(maxsize=1)
def get_db() -> Database:
    settings = json.loads(
        (ROOT / "settings.json").read_text(encoding="utf-8")
    )
    return Database(str(ROOT / settings["db_path"]))

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
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    Database(str(ROOT / settings["db_path"])).reset_ignored()
    return {"words": cleaned}


@app.get("/api/logs/{name}")
def get_logs(name: str, lines: int = Query(150, ge=1, le=1000)):
    if name not in ("parse", "notify"):
        raise HTTPException(400, "only parse or notify")
    return {"name": name, "text": tail(ROOT / f"{name}.log", lines)}

@app.get("/api/calendar")
def get_calendar(
    year: int = Query(..., ge=1, le=9999),
    month: int = Query(..., ge=1, le=12),
):
    return get_db().get_calendar_month(year, month)


@app.put("/api/calendar/days/{day}")
def put_calendar_day(day: date, payload: CalendarDayIn):
    db = get_db()
    db.set_non_working_day(
        day=day,
        is_non_working=payload.is_non_working,
        description=payload.description,
    )
    return db.get_calendar_month(day.year, day.month)


@app.put("/api/calendar/months/{year}/{month}")
def put_calendar_month(
    payload: CalendarMonthIn,
    year: int = ApiPath(..., ge=1, le=9999),
    month: int = ApiPath(..., ge=1, le=12),
):
    db = get_db()
    db.set_month_ready(
        year=year,
        month=month,
        is_ready=payload.is_ready,
    )
    return db.get_calendar_month(year, month)