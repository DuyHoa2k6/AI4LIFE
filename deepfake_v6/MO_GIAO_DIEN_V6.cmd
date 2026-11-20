@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo ScamShield Deepfake v6 - trinh duyet se tu mo http://127.0.0.1:8011/
echo Dong cua so nay de tat.
start "" cmd /c "timeout /t 10 /nobreak >nul & start http://127.0.0.1:8011/"
.venv\Scripts\python.exe -m uvicorn web_v6:app --host 127.0.0.1 --port 8011 --no-access-log
pause
