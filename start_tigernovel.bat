@echo off
setlocal

REM TigerNovel Windows launcher
REM Usage:
REM   start_tigernovel.bat create-book --slug my-book --title "我的小说"
REM   start_tigernovel.bat write-chapter --slug my-book --chapter 1 --chapter-title "雨夜来客"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

if "%~1"=="" goto :help

if exist ".venv\Scripts\tigernovel.exe" (
  ".venv\Scripts\tigernovel.exe" %*
  set "EXIT_CODE=%ERRORLEVEL%"
  goto :end
)

if exist ".venv\Scripts\python.exe" (
  set "PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%"
  ".venv\Scripts\python.exe" -m app.cli %*
  set "EXIT_CODE=%ERRORLEVEL%"
  goto :end
)

echo [TigerNovel] .venv not found.
echo Please run:
echo   python -m venv .venv
echo   .venv\Scripts\Activate.ps1
echo   pip install -e .[dev]
set "EXIT_CODE=1"
goto :end

:help
echo TigerNovel Launcher

echo.
echo Usage:
echo   start_tigernovel.bat create-book --slug my-book --title "我的小说"
echo   start_tigernovel.bat write-chapter --slug my-book --chapter 1 --chapter-title "雨夜来客"
set "EXIT_CODE=0"

:end
popd >nul
exit /b %EXIT_CODE%
