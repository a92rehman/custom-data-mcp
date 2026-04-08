@echo off
REM Windows shim to run session-start hook
REM Mirrors the pattern used by superpowers plugin
set "HOOK_DIR=%~dp0%1"
if exist "%HOOK_DIR%\update.sh" (
  bash "%HOOK_DIR%\update.sh"
)
