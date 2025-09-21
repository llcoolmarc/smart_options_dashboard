@echo off
cd /d %%~dp0
set "PY=%C:\Users\Owner\AppData\Local%\Programs\Python\Python310\python.exe"
if not exist "%%PY%%" set "PY=python"
"%%PY%%" -m pip install -q dash plotly python-dotenv requests
"%%PY%%" app.py
pause
