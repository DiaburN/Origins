@echo off
setlocal
cd /d "%~dp0"

if not exist INPUT_HPR mkdir INPUT_HPR
if not exist OUTPUT_HISPA_ZIRCON mkdir OUTPUT_HISPA_ZIRCON

echo.
echo ================================================
echo   ORIGINS HPR -^> ZIRCON MONSTER BUILDER V2
echo ================================================
echo.
echo 1. Copia las .hpr dentro de INPUT_HPR
echo 2. Recomendado: crea ANALYSIS y mete ahi el analisis anterior
echo    que contiene CURSOR_PROFILE.json de las 650 Hispa.
echo.

py -m pip install -r requirements.txt
if errorlevel 1 goto :error

set ANALYSIS_ARG=
if exist ANALYSIS set ANALYSIS_ARG=--analysis-root ANALYSIS

py origins_hpr_zircon_v2.py batch INPUT_HPR --out OUTPUT_HISPA_ZIRCON %ANALYSIS_ARG%
if errorlevel 1 goto :error

echo.
echo TERMINADO.
echo Abre: OUTPUT_HISPA_ZIRCON\MASTER_SHEET.html
echo.
pause
exit /b 0

:error
echo.
echo ERROR. Revisa el mensaje anterior y OUTPUT_HISPA_ZIRCON\FAILURES.json si existe.
echo.
pause
exit /b 1
