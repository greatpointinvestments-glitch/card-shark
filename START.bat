@echo off
title CardHawk
echo.
echo  =============================
echo    CardHawk is starting...
echo  =============================
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run app.py
pause
