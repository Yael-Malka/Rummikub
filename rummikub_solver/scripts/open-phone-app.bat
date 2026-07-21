@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0deploy-phone.ps1" -LaunchOnly
pause
