@echo off
setlocal

set "GENIE_ROOT=%~dp0"
set "GENIE_PYTHON=%GENIE_ROOT%Runtime\.venv\Scripts\python.exe"
set "GENIE_WEBUI=%GENIE_ROOT%Scripts\start-webui.py"

if not exist "%GENIE_PYTHON%" (
    echo Internal Python was not found: %GENIE_PYTHON%
    pause
    exit /b 1
)

if not exist "%GENIE_WEBUI%" (
    echo WebUI launcher was not found: %GENIE_WEBUI%
    pause
    exit /b 1
)

pushd "%GENIE_ROOT%" >nul
"%GENIE_PYTHON%" "%GENIE_WEBUI%" %*
set "GENIE_EXIT=%ERRORLEVEL%"
popd >nul

if not "%GENIE_EXIT%" == "0" (
    echo.
    echo Genie-TTS WebUI exited with code %GENIE_EXIT%.
    pause
)

exit /b %GENIE_EXIT%
