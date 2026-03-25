@echo off
echo ========================================
echo   BUILD - Gestion de Pases Automaticos
echo ========================================
echo.

rem Cambiar al directorio del script (donde está el código)
cd /d "%~dp0"
echo Directorio de trabajo: %CD%
echo.

rem Limpiar builds anteriores
echo [1/4] Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del *.spec

rem Build con PyInstaller
echo [2/4] Compilando exe...
pyinstaller --name "GestionPases" ^
    --onedir ^
    --add-data "config;config" ^
    --add-data "tui;tui" ^
    --collect-all textual ^
    --collect-all playwright ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Falló la compilación
    pause
    exit /b 1
)

rem Copiar browsers de Playwright
echo [3/4] Copiando Chromium...
xcopy /s /e /y "%LOCALAPPDATA%\ms-playwright\chromium-*" "dist\GestionPases\_internal\ms-playwright\" >nul

rem Crear ZIP
echo [4/4] Creando ZIP para distribuir...
powershell -Command "Compress-Archive -Path 'dist\GestionPases' -DestinationPath 'dist\GestionPases.zip' -CompressionLevel Optimal -Force"

echo.
echo ========================================
echo   BUILD COMPLETADO EXITOSAMENTE
echo ========================================
echo.
echo Archivos generados:
echo   - dist\GestionPases\      (carpeta para probar)
echo   - dist\GestionPases.zip   (ZIP para distribuir)
echo.
pause