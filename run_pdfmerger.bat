@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 pdfmerger_desktop.py
  goto done
)

where python >nul 2>nul
if %errorlevel%==0 (
  python pdfmerger_desktop.py
  goto done
)

echo Python was not found.
echo Install Python 3.9 or newer, then run:
echo   python -m pip install -r requirements.txt
pause

:done
endlocal
