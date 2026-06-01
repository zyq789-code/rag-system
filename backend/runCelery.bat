@echo off
cd /d "%~dp0"
chcp 65001
call venv\Scripts\activate
python Celery.py
pause