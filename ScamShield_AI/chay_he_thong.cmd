@echo off
cd /d "%~dp0"
echo ScamShield AI - Mo http://127.0.0.1:8000
echo Nhan Ctrl+C de dung. Neu cong 8000 dang dung, hay dung server cu truoc.
python -m uvicorn backend.main:app --app-dir . --host 127.0.0.1 --port 8000 --no-access-log
pause
