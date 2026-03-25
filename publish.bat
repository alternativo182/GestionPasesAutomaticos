@echo off
echo ========================================
echo   PUBLISH - Gestion de Pases Automaticos
echo ========================================
echo.

rem Cambiar al directorio del script
cd /d "%~dp0"

rem Pedir versión
set /p VERSION="Ingresá la versión (ej: 1.0.1): "
if "%VERSION%"=="" (
    echo ERROR: No se ingresó versión
    pause
    exit /b 1
)

echo.
echo Versión a publicar: v%VERSION%
echo.

rem Limpiar builds anteriores
echo [1/5] Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del *.spec

rem Build con PyInstaller
echo [2/5] Compilando exe...
pyinstaller --name "GestionPases" ^
    --onedir ^
    --add-data "config;config" ^
    --add-data "tui;tui" ^
    --collect-all textual ^
    --collect-all playwright ^
    main.py

if errorlevel 1 (
    echo ERROR: Falló la compilación
    pause
    exit /b 1
)

rem Copiar browsers de Playwright
echo [3/5] Copiando Chromium...
xcopy /s /e /y "%LOCALAPPDATA%\ms-playwright\chromium-*" "dist\GestionPases\_internal\ms-playwright\" >nul

rem Crear ZIP
echo [4/5] Creando ZIP...
powershell -Command "Compress-Archive -Path 'dist\GestionPases' -DestinationPath 'dist\GestionPases.zip' -CompressionLevel Optimal -Force"

rem Crear Release en GitHub
echo [5/5] Publicando en GitHub Releases...
gh release create v%VERSION% "dist\GestionPases.zip" ^
    --title "GestionPases v%VERSION%" ^
    --notes "Versión %VERSION% empaquetada como .exe" ^
    --target dev

if errorlevel 1 (
    echo ERROR: Falló la publicación en GitHub
    echo Verificá que estás autenticado con: gh auth login
    pause
    exit /b 1
)

echo.
echo ========================================
echo   PUBLICACIÓN COMPLETADA
echo ========================================
echo.
echo  Versión: v%VERSION%
echo  Release: https://github.com/alternativo182/GestionPasesAutomaticos/releases/tag/v%VERSION%
echo.
echo  Instalación remota:
echo  irm https://raw.githubusercontent.com/alternativo182/GestionPasesAutomaticos/main/install.ps1 ^| iex
echo.
pause