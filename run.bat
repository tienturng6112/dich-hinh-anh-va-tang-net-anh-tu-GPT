@echo off
cd /d "%~dp0"
title AI Image Translator and Enhancer (ChatGPT)
echo ========================================================
echo   KHOI DONG UNG DUNG DICH ANH VA LAM NET QUA CHATGPT
echo ========================================================
echo.
echo Dang khoi chay ung dung, vui long doi giay lat...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the khoi chay ung dung. Ma loi: %ERRORLEVEL%
    echo Vui long kiem tra lai moi truong Python.
    pause
)
