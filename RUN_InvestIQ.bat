@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
set PYTHONPATH=.
streamlit run src\investment_guru\ui\app.py
pause
