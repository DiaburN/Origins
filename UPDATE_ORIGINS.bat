@echo off
setlocal
cd /d "%~dp0"

echo [1/7] Descargando actualizaciones...
git pull
if errorlevel 1 goto :error

echo.
echo [2/7] Generando interfaz Zircon desde los archivos originales...
py tools\mir3\build_full_zircon_ui.py
if errorlevel 1 goto :error

echo.
echo [3/7] Generando primitives exactos de Interface.Zl...
py tools\mir3\build_zircon_primitives.py
if errorlevel 1 goto :error

echo.
echo [4/7] Reconstruyendo MainPanel GameInter exacto...
py tools\mir3\build_mainpanel_runtime.py
if errorlevel 1 goto :error

echo.
echo [5/7] Buscando ProgUse.Zl para el paperdoll de personaje...
py tools\mir3\build_character_paperdoll_runtime.py
if errorlevel 1 goto :error

echo.
echo [6/7] Generando magias reales desde System.db + MIcon.Zl...
py tools\mir3\build_magic_runtime.py
if errorlevel 1 goto :error

echo.
echo [7/7] ORIGINS X actualizado.
echo Abriendo servidor local en http://localhost:5500
start "" http://localhost:5500
py -m http.server 5500
goto :eof

:error
echo.
echo ERROR: no se pudo completar la actualizacion.
echo.
echo Si no encuentra los .Zl de interfaz, ejecuta:
echo py tools\mir3\build_full_zircon_ui.py --source "C:\ruta\a\Data"
echo py tools\mir3\build_zircon_primitives.py --source "C:\ruta\a\Data"
echo py tools\mir3\build_mainpanel_runtime.py --source "C:\ruta\a\Data"
echo py tools\mir3\build_character_paperdoll_runtime.py --source "C:\ruta\a\Data"
echo.
echo Si falla el menu Magic, apunta al directorio que contenga System.db y MIcon.Zl:
echo py tools\mir3\build_magic_runtime.py --source "C:\ruta\a\la\referencia"
pause
exit /b 1
