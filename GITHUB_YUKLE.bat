@echo off
chcp 65001 >nul
title Açık Arttırma - GitHub'a Yükleme & Yedekleme
color 0A

echo =======================================================================
echo          AÇIK ARTTIRMA — GITHUB & ARŞİVİZM YEDEKLEME
echo =======================================================================
echo.
echo [*] Değişiklikler kaydediliyor...
cd /d "%~dp0"
git add -A
git commit -m "update: acik arttirma web guncellemeleri" >nul 2>&1

echo [*] GitHub'a pushlanıyor...
git push origin main

echo [*] 3 Katmanlı Arşivizm Yedek Yöneticisi çalıştırılıyor...
py C:\Users\akkus\arsivizm_backups\backup_manager.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo [+] TEBRİKLER! Tüm dosyalar GitHub'a ve yerel yedek kasasına kaydedildi!
    echo =======================================================================
) else (
    echo.
    echo [!] Yedekleme sırasında bir uyarı oluştu.
)

echo.
pause
