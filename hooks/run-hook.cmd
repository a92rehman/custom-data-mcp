@echo off
REM Windows shim to run session-start hook
REM Prefers Python (cross-platform), falls back to bash
set "HOOK_DIR=%~dp0%1"

REM Try Python first (avoids bash.exe crashes on Windows)
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
  if exist "%HOOK_DIR%\update.py" (
    python "%HOOK_DIR%\update.py"
    exit /b 0
  )
)

REM Fallback to bash
if exist "%HOOK_DIR%\update.sh" (
  bash "%HOOK_DIR%\update.sh"
)
