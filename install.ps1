<#
.SYNOPSIS
    Instala GestionPasesAutomaticos desde GitHub Releases
.DESCRIPTION
    Descarga, extrae y configura la aplicación automáticamente.
    El browser Chromium se instala en cache local la PRIMERA VEZ.
    Uso: irm https://raw.githubusercontent.com/alternativo182/GestionPasesAutomaticos/main/install.ps1 | iex
#>

# Configuración
$Repo = "alternativo182/GestionPasesAutomaticos"
$AppName = "GestionPases"
$InstallDir = "$env:LOCALAPPDATA\GestionPases"
$CacheDir = "$env:LOCALAPPDATA\GestionPases\cache\ms-playwright"
$BrowserVersion = "chromium-1208"

# Colores para output
function Write-Step { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Warn { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }

Clear-Host
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   GESTION DE PASES - INSTALADOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 1. Verificar/Instalar browser Chromium (solo la primera vez)
    $browserExe = "$CacheDir\$BrowserVersion\chrome-win64\chrome.exe"
    if (-not (Test-Path $browserExe)) {
        Write-Step "Primera instalación: configurando browser Chromium..."
        Write-Warn "Esto descargará ~400MB solo la primera vez"
        
        # Crear directorio de cache
        New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
        
        # Descargar browser desde el CDN de Playwright
        Write-Step "Descargando Chromium (~400MB)..."
        $browserUrl = "https://playwright.azureedge.net/builds/chromium/1155/chromium-win64.zip"
        $browserZip = "$env:TEMP\chromium.zip"
        
        try {
            # Intentar descargar desde CDN de Playwright
            Invoke-WebRequest -Uri $browserUrl -OutFile $browserZip -UseBasicParsing
        } catch {
            # Si falla, mostrar instrucciones manuales
            Write-Warn "No se pudo descargar automáticamente."
            Write-Host ""
            Write-Host "  Instale Chromium manualmente:" -ForegroundColor Yellow
            Write-Host "  1. Abra PowerShell como administrador" -ForegroundColor Yellow
            Write-Host "  2. Ejecute: npx playwright install chromium" -ForegroundColor Yellow
            Write-Host "  3. O descargue desde: https://playwright.dev/docs/browsers" -ForegroundColor Yellow
            Write-Host ""
            
            # Intentar usar npx playwright install
            Write-Step "Intentando instalar con Playwright CLI..."
            $env:PLAYWRIGHT_BROWSERS_PATH = $CacheDir
            npx playwright install chromium
            if (Test-Path $browserExe) {
                Write-Ok "Browser instalado correctamente"
            } else {
                Write-Warn "Continuando sin browser - se intentará al ejecutar la app"
            }
        } finally {
            if (Test-Path $browserZip) {
                Remove-Item $browserZip -Force
            }
        }
        
        # Si se descargó el zip, extraerlo
        if (Test-Path $browserZip) {
            Write-Step "Extrayendo Chromium..."
            Expand-Archive -Path $browserZip -DestinationPath $CacheDir -Force
            Remove-Item $browserZip -Force
        }
        
        if (Test-Path $browserExe) {
            Write-Ok "Browser instalado en: $CacheDir"
        }
    } else {
        Write-Ok "Browser Chromium ya instalado en cache"
    }
    
    # 2. Obtener última release
    Write-Step "Buscando última versión..."
    $release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
    $version = $release.tag_name
    $asset = $release.assets | Where-Object { $_.name -like "*$AppName*.zip" } | Select-Object -First 1
    
    if (-not $asset) {
        Write-Error "No se encontró el archivo $AppName.zip en la release $version"
        exit 1
    }
    
    Write-Ok "Versión encontrada: $version"
    
    # 3. Crear directorio de instalación
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
    
    # 4. Descargar (sin Chromium - solo exe + dependencias Python)
    Write-Step "Descargando $AppName v$version ($([math]::Round($asset.size/1MB, 1)) MB)..."
    $zipPath = "$env:TEMP\$AppName.zip"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing
    Write-Ok "Descarga completada"
    
    # 5. Extraer
    Write-Step "Extrayendo archivos..."
    Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
    Remove-Item $zipPath -Force
    Write-Ok "Archivos extraídos"
    
    # 6. Crear shortcuts
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
    
    # 7. Resumen
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   INSTALACIÓN COMPLETADA" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Versión:     $version"
    Write-Host "  Ubicación:   $InstallDir\$AppName"
    Write-Host "  Ejecutable:  GestionPases.exe"
    Write-Host "  Browser:     $CacheDir (cache local)"
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