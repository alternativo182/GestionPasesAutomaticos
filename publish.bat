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

rem Actualizar versión en update_checker.py
echo [1/6] Actualizando versión en update_checker.py...
powershell -Command "(Get-Content 'utils\update_checker.py') -replace '__version__ = \"[^\"]*\"', '__version__ = \"%VERSION%\"' | Set-Content 'utils\update_checker.py'"
echo [OK] Versión actualizada a %VERSION%

rem Limpiar builds anteriores
echo [2/6] Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del *.spec

rem Build con PyInstaller
echo [3/6] Compilando exe...
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
echo [4/6] Copiando Chromium...
xcopy /s /e /y "%LOCALAPPDATA%\ms-playwright\chromium-*" "dist\GestionPases\_internal\ms-playwright\" >nul

rem Crear ZIP
echo [5/6] Creando ZIP...
powershell -Command "Compress-Archive -Path 'dist\GestionPases' -DestinationPath 'dist\GestionPases.zip' -CompressionLevel Optimal -Force"

rem Commit y push de la nueva versión
echo [6/6] Guardando cambios en Git...
git add utils/update_checker.py
git commit -m "chore: actualizar versión a v%VERSION%"
git push origin dev
git checkout main
git merge dev
git push origin main
git checkout dev

rem Crear Release en GitHub
echo.
echo Publicando Release v%VERSION% en GitHub...
gh release create v%VERSION% "dist\GestionPases.zip" ^
    --title "GestionPases v%VERSION%" ^
    --notes "Versión %VERSION% empaquetada como .exe" ^
    --target main

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