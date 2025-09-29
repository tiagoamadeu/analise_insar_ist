@echo off
cd /d "%~dp0"

REM Ativar ambiente virtual
call "venv-snap\Scripts\activate.bat"

REM Executar Streamlit na pasta app
python -m streamlit run "app\app.py"

pause




