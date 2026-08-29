@echo off
cd /d "%~dp0"
chcp 65001
call venv\Scripts\activate
rem HuggingFace 模型已手动缓存，强制离线加载
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
python Celery.py
pause