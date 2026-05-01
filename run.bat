@echo off
REM ============================================
REM Security Workshop — Quick Start (Windows)
REM ============================================
REM Prerequisites: Python 3.8+

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting servers...
echo    Victim app:   http://localhost:5000
echo    Attacker app: http://localhost:5001
echo    Flag checker: http://localhost:5000/flags
echo.
echo    Close this window to stop both servers.
echo.

start /B python victim\app.py
start /B python attacker\app.py

echo Servers running. Press Ctrl+C to stop.
pause > nul
