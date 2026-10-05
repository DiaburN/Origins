@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title ORIGINS HPR - ZIRCON MASTER BUILDER

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No encuentro Python Launcher ^(py.exe^).
  echo Instala Python 3.10+ y marca Add Python to PATH.
  pause
  exit /b 1
)

py -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo Instalando Pillow...
  py -m pip install -r requirements.txt
  if errorlevel 1 goto :fail
)

:menu
cls
echo ================================================================
echo        ORIGINS HPR -^> ZIRCON MASTER BUILDER
echo ================================================================
echo.
echo   [1] Crear MASTER SHEET desde analisis ya generado
echo   [2] Construir .Zl de UN monstruo preparado
echo   [3] Analizar carpeta HPR con backend monster_hpr_analyzer.py
echo   [4] Validar carpeta de UN monstruo
echo   [5] Salir
echo.
set /p OP=Elige opcion: 
if "%OP%"=="1" goto :master
if "%OP%"=="2" goto :build
if "%OP%"=="3" goto :analyze
if "%OP%"=="4" goto :validate
if "%OP%"=="5" exit /b 0
goto :menu

:master
cls
echo --- MASTER SHEET ---
set /p AR=Carpeta del analisis: 
set /p MF=Ruta ALL_MONSTERS_CURSOR_MANIFEST.json ^(ENTER si no tienes^): 
set /p OUT=Carpeta de salida MASTER: 
if "%MF%"=="" (
  py origins_hpr_zircon_builder.py master --analysis-root "%AR%" --output "%OUT%"
) else (
  py origins_hpr_zircon_builder.py master --analysis-root "%AR%" --manifest "%MF%" --output "%OUT%"
)
goto :result

:build
cls
echo --- BUILD .Zl ---
set /p MR=Carpeta del monstruo preparado: 
set /p OUT=Carpeta de salida: 
py origins_hpr_zircon_builder.py build --monster-root "%MR%" --output "%OUT%"
goto :result

:analyze
cls
echo --- ANALYZE HPR ---
set /p HR=Carpeta con .hpr: 
set /p OUT=Carpeta de analisis: 
set /p MASTER=Carpeta MASTER final ^(ENTER para no crearla ahora^): 
if "%MASTER%"=="" (
  py origins_hpr_zircon_builder.py analyze --hpr-root "%HR%" --output "%OUT%"
) else (
  py origins_hpr_zircon_builder.py analyze --hpr-root "%HR%" --output "%OUT%" --master-output "%MASTER%"
)
goto :result

:validate
cls
echo --- VALIDATE ---
set /p MR=Carpeta del monstruo: 
py origins_hpr_zircon_builder.py validate --monster-root "%MR%"
goto :result

:result
if errorlevel 1 (
  echo.
  echo [ERROR] El proceso termino con errores. Lee el mensaje anterior.
) else (
  echo.
  echo [OK] Proceso terminado.
)
pause
goto :menu

:fail
echo.
echo [ERROR] No se pudo preparar el entorno.
pause
exit /b 1
