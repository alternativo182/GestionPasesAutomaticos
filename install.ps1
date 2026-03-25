<#
.SYNOPSIS
    Instala GestionPasesAutomaticos desde GitHub Releases
.DESCRIPTION
    Descarga, extrae y configura la aplicación automáticamente.
    Uso: irm https://raw.githubusercontent.com/alternativo182/GestionPasesAutomaticos/main/install.ps1 | iex
#>

# Configuración
$Repo = "alternativo182/GestionPasesAutomaticos"
$AppName = "GestionPases"
$InstallDir = "$env:LOCALAPPDATA\GestionPases"

# Colores para output
function Write-Step { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

Clear-Host
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   GESTION DE PASES - INSTALADOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 1. Obtener última release
    Write-Step "Buscando última versión..."
    $release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
    $version = $release.tag_name
    $asset = $release.assets | Where-Object { $_.name -like "*$AppName*.zip" } | Select-Object -First 1
    
    if (-not $asset) {
        Write-Error "No se encontró el archivo $AppName.zip en la release $version"
        exit 1
    }
    
    Write-Ok "Versión encontrada: $version"
    
    # 2. Crear directorio de instalación
    Write-Step "Preparando directorio de instalación..."
    
    # Esperar a que el proceso GestionPases.exe se cierre si está ejecutándose
    $maxAttempts = 10
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        $process = Get-Process -Name "GestionPases" -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "[*] Esperando que se cierre GestionPases..." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
            $attempt++
        } else {
            break
        }
    }
    
    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Write-Ok "Directorio: $InstallDir"
    
    # 3. Descargar
    Write-Step "Descargando $AppName ($([math]::Round($asset.size/1MB, 1)) MB)..."
    $zipPath = "$env:TEMP\$AppName.zip"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing
    Write-Ok "Descarga completada"
    
    # 4. Extraer
    Write-Step "Extrayendo archivos..."
    Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
    Remove-Item $zipPath -Force
    Write-Ok "Archivos extraídos"
    
    # 5. Crear shortcuts
    Write-Step "Creando accesos directos..."
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Start Menu
    $startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    $shortcutMenu = $WshShell.CreateShortcut("$startMenu\$AppName.lnk")
    $shortcutMenu.TargetPath = "$InstallDir\$AppName\GestionPases.exe"
    $shortcutMenu.WorkingDirectory = "$InstallDir\$AppName"
    $shortcutMenu.Description = "Gestión de Pases Automáticos - SICO"
    $shortcutMenu.Save()
    Write-Ok "Acceso directo creado en Menú Inicio"
    
    # Desktop
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcutDesk = $WshShell.CreateShortcut("$desktop\$AppName.lnk")
    $shortcutDesk.TargetPath = "$InstallDir\$AppName\GestionPases.exe"
    $shortcutDesk.WorkingDirectory = "$InstallDir\$AppName"
    $shortcutDesk.Description = "Gestión de Pases Automáticos - SICO"
    $shortcutDesk.Save()
    Write-Ok "Acceso directo creado en Escritorio"
    
    # 6. Resumen
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   INSTALACIÓN COMPLETADA" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Versión:     $version"
    Write-Host "  Ubicación:   $InstallDir\$AppName"
    Write-Host "  Ejecutable:  GestionPases.exe"
    Write-Host ""
    Write-Host "  Puedes ejecutarlo desde:"
    Write-Host "  - El acceso directo en Menú Inicio"
    Write-Host "  - Doble click en $InstallDir\$AppName\GestionPases.exe"
    Write-Host ""
    
    # Preguntar si quiere ejecutar ahora
    $response = Read-Host "¿Deseas ejecutar la aplicación ahora? (S/N)"
    if ($response -eq 'S' -or $response -eq 's') {
        Start-Process "$InstallDir\$AppName\GestionPases.exe"
    }
}
catch {
    Write-Error "Error durante la instalación: $_"
    exit 1
}