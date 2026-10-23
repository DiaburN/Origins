@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Descargando actualizaciones...
git pull
if errorlevel 1 goto :error

echo.
echo [2/3] Generando interfaz Zircon desde los archivos originales...
py tools\mir3\build_full_zircon_ui.py
if errorlevel 1 goto :error

echo.
echo [3/3] ORIGINS X actualizado.
echo Abriendo servidor local en http://localhost:5500
start "" http://localhost:5500
py -m http.server 5500
goto :eof

:error
echo.
echo ERROR: no se pudo completar la actualizacion.
echo Si no encuentra los .Zl, ejecuta:
echo py tools\mir3\build_full_zircon_ui.py --source "C:\ruta\a\Data"
pause
exit /b 1
