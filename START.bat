@echo off
title Card Shark
echo.
echo  =============================
echo    Card Shark is starting...
echo  =============================
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run app.py
pause
