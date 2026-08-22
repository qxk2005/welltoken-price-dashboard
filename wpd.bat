@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0bin\wpd.ps1" -Action "%~1"
