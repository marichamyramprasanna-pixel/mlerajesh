@echo off
setlocal
cd /d "%~dp0"
set "PORT=8512"
set "BACKEND_PORT=8520"
set "URL=http://localhost:%PORT%"

if exist "%~dp0.venv\Scripts\python.exe" (
  set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo Python is not installed or not on PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
  )
  set "PYTHON_EXE=python"
)

start "Machine Fault Diagnosis Backend" /min "%PYTHON_EXE%" -m uvicorn backend:app --host 0.0.0.0 --port %BACKEND_PORT%

start "Machine Fault Diagnosis Server" /min "%PYTHON_EXE%" -m streamlit run app.py --server.headless true --server.port %PORT% --server.address 0.0.0.0 --browser.gatherUsageStats false

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 60;$i++){try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',%PORT%);$c.Close();$ok=$true;break}catch{};Start-Sleep -Milliseconds 500}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo The application server did not start.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 60;$i++){try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',%BACKEND_PORT%);$c.Close();$ok=$true;break}catch{};Start-Sleep -Milliseconds 250}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo The backend server did not start.
  pause
  exit /b 1
)

set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 60;$i++){try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',%BACKEND_PORT%);$c.Close();$ok=$true;break}catch{};Start-Sleep -Milliseconds 250}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo The backend server did not start.
  pause
  exit /b 1
)

set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 60;$i++){try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',%BACKEND_PORT%);$c.Close();$ok=$true;break}catch{};Start-Sleep -Milliseconds 250}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo The backend server did not start.
  pause
  exit /b 1
)

set "EDGE=%LocalAppData%\Microsoft\Edge\Application\msedge.exe"

set "INTRO=file:///%~dp0intro.html"
set "INTRO=%INTRO:\=/%"

if exist "%EDGE%" (
  start "Machine Fault Diagnosis" "%EDGE%" --app="%INTRO%" --start-maximized
  exit /b 0
)

set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if exist "%CHROME%" (
  start "Machine Fault Diagnosis" "%CHROME%" --app="%INTRO%" --start-maximized
  exit /b 0
)

start "" "%INTRO%"
exit /b 0
