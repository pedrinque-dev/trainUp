@echo off
cd /d "%~dp0backend"
if not exist venv (
  py -3.12 -m venv venv || py -3 -m venv venv || python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo API em http://127.0.0.1:8000/api/docs
uvicorn app.main:app --reload
