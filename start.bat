@echo off
cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

set PYTHONPATH=src

start "parser" cmd /k python scripts\parse.py