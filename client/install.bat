@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "EXE_PATH=%SCRIPT_DIR%dist\RapidShare.exe"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=RapidShare.vbs"

echo === rapid_share Setup ===

REM EXEがあればそちらを使う
if exist "%EXE_PATH%" (
    echo Using pre-built EXE: %EXE_PATH%
    echo Creating startup script...
    (
        echo Set WshShell = CreateObject^("WScript.Shell"^)
        echo WshShell.Run """%EXE_PATH%""", 0, False
    ) > "%STARTUP_DIR%\%SHORTCUT_NAME%"
    echo.
    echo Setup complete!
    echo   - Startup: %STARTUP_DIR%\%SHORTCUT_NAME%
    echo   - Config:  %SCRIPT_DIR%config.json
    echo.
    echo Starting...
    start "" "%EXE_PATH%"
    pause
    exit /b
)

REM EXEがなければvenvで実行
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv "%VENV_DIR%"
)

echo Installing dependencies...
"%VENV_DIR%\Scripts\pip" install -q -r "%SCRIPT_DIR%requirements.txt"

echo Creating startup script...
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.CurrentDirectory = "%SCRIPT_DIR%"
echo WshShell.Run """%VENV_DIR%\Scripts\pythonw.exe"" ""%SCRIPT_DIR%data_share_client.py""", 0, False
) > "%STARTUP_DIR%\%SHORTCUT_NAME%"

echo.
echo Setup complete!
echo   - Startup: %STARTUP_DIR%\%SHORTCUT_NAME%
echo   - Config:  %SCRIPT_DIR%config.json
echo.
echo Starting...
start "" "%VENV_DIR%\Scripts\pythonw.exe" "%SCRIPT_DIR%data_share_client.py"
pause
