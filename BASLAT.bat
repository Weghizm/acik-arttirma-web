@echo off
chcp 65001 >nul
title Açık Arttırma — Canlı Müzayede Oyunu
color 0B

echo =======================================================================
echo          AÇIK ARTTIRMA — CANLI ÇOK OYUNCULU MÜZAYEDE OYUNU
echo =======================================================================
echo.

:: 1. Python Kontrolü
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] HATA: Bilgisayarınızda Python bulunamadı!
    echo Lütfen Python'un kurulu ve PATH'e ekli olduğundan emin olun.
    pause
    exit /b 1
)

:: 2. Kütüphane Kontrolü
python -c "import fastapi, uvicorn, websockets, requests" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Gerekli kütüphaneler kuruluyor, lütfen bekleyin...
    pip install -r "%~dp0requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo [!] Kütüphane kurulumunda hata oluştu.
        pause
        exit /b 1
    )
    echo [+] Kurulum tamamlandı!
    echo.
)

:: 3. Port 8000 kontrolü ve temizleme
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [*] Port 8000 üzerindeki eski oturum kapatılıyor (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: 4. Tarayıcıyı Aç ve Sunucuyu Başlat
echo [*] Sunucu başlatılıyor: http://localhost:8000
echo [*] Tarayıcı 2 saniye içinde açılacak...
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"
cd /d "%~dp0"
python server.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Sunucu beklenmeyen şekilde kapandı.
    pause
)
