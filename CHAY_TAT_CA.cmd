@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "REPO=%~dp0"
set "V6=%~dp0deepfake_v6"
set "V6FALLBACK=%~dp0..\muse_v6_light"
if not exist "%V6%\web_v6.py" if exist "%V6FALLBACK%\web_v6.py" set "V6=%V6FALLBACK%"
set "V6PY=%V6%\.venv\Scripts\python.exe"
if not exist "%V6PY%" if exist "%V6FALLBACK%\.venv\Scripts\python.exe" set "V6PY=%V6FALLBACK%\.venv\Scripts\python.exe"
set PYTHONUTF8=1

echo ============================================
echo  ScamShield AI + Deepfake v6
echo  Web:      http://127.0.0.1:8000/
echo  Deepfake: http://127.0.0.1:8000/deepfake
echo  Dong hai cua so server de tat.
echo.
echo  Extension (Edge): mo edge://extensions
echo    - Bat "Che do nha phat trien"
echo    - Load unpacked (hoac Reload neu da nap):
echo      %~dp0ScamShield_AI\extension
echo  Day la lenh khoi dong duy nhat cho web va extension
echo  (kiem tra tin nhan + deepfake anh/video/cuoc goi).
echo ============================================

if exist "%V6%\web_v6.py" if not exist "%V6%\weights\ms_eff_gcvit_b0_ff++.bin" (
  if exist "%V6FALLBACK%\weights\ms_eff_gcvit_b0_ff++.bin" (
    if not exist "%V6%\weights" (
      echo Dung weights tu muse_v6_light ...
      mklink /J "%V6%\weights" "%V6FALLBACK%\weights" >nul 2>&1
    )
  ) else (
    echo Chua co weights. Neu can, chay: "%V6PY%" "%V6%\download_weights.py"
  )
)

netstat -ano | findstr "LISTENING" | findstr ":8011" >nul
if errorlevel 1 (
  echo Dang mo Deepfake v6 tren cong 8011 ...
  start "ScamShield Deepfake v6" /D "%V6%" cmd /k "set PYTHONUTF8=1&& "%V6PY%" -m uvicorn web_v6:app --host 127.0.0.1 --port 8011 --no-access-log"
) else (
  echo Deepfake v6 da chay tren cong 8011.
)

netstat -ano | findstr "LISTENING" | findstr ":8000" >nul
if errorlevel 1 (
  echo Dang mo backend nhom tren cong 8000 ...
  start "ScamShield AI" /D "%REPO%" cmd /k "set PYTHONUTF8=1&& .venv\Scripts\python.exe -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log"
) else (
  echo Backend nhom da chay tren cong 8000.
)

echo Cho server san sang (v6 co the mat 30-90 giay de tai mo hinh)...
powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 90;$i++){ try { $a=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 2; $b=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8011/api/deepfake/health -TimeoutSec 2; if($a.StatusCode -eq 200 -and $b.StatusCode -eq 200){ $ok=$true; break } } catch {} ; Start-Sleep -Seconds 1 }; if($ok){ 'San sang.' } else { 'Het thoi gian cho. Mo trinh duyet; neu trang deepfake bao chua san sang thi doi them roi tai lai.' }"

start http://127.0.0.1:8000/
start http://127.0.0.1:8000/deepfake
echo Da mo trinh duyet. Cua so nay co the dong.
endlocal
