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
$BaseDir = "$env:LOCALAPPDATA\GestionPases"          # Directorio base
$InstallDir = "$BaseDir\app"                         # Programa (se reemplaza en updates)
$DataDir = "$BaseDir\data"                           # Datos del usuario (PERSISTE)
$CacheDir = "$BaseDir\cache\ms-playwright"           # Browser Chromium (PERSISTE)

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
    # Buscar si ya existe algún chromium instalado
    $existingChrome = Get-ChildItem -Path $CacheDir -Recurse -Filter "chrome.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if (-not $existingChrome) {
        Write-Step "Primera instalación: configurando browser Chromium..."
        Write-Warn "Esto descargará ~400MB solo la primera vez"
        
        # Crear directorio de cache
        New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
        
        # Descargar browser usando Playwright CLI (instala la versión correcta automáticamente)
        Write-Step "Descargando Chromium (~400MB)..."
        
        try {
            # Usar npx playwright install que descarga la versión correcta automáticamente
            $env:PLAYWRIGHT_BROWSERS_PATH = $CacheDir
            & npx.cmd playwright install chromium 2>&1 | Out-Null
        } catch {
            Write-Warn "No se pudo descargar automáticamente."
            Write-Host ""
            Write-Host "  Instale Chromium manualmente:" -ForegroundColor Yellow
            Write-Host "  1. Ejecute: npx playwright install chromium" -ForegroundColor Yellow
            Write-Host "  2. O descargue desde: https://playwright.dev/docs/browsers" -ForegroundColor Yellow
            Write-Host ""
        }
        
        # Verificar si se instaló
        $existingChrome = Get-ChildItem -Path $CacheDir -Recurse -Filter "chrome.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($existingChrome) {
            Write-Ok "Browser instalado en: $($existingChrome.DirectoryName)"
        } else {
            Write-Warn "Browser no encontrado. La app podría no funcionar."
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
    
    # 3. Crear directorios necesarios
    Write-Step "Preparando directorios..."
    
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
    
    # Crear directorios (data y cache persisten entre actualizaciones)
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    
    # Migrar DB desde ubicación vieja si existe (compatibilidad hacia atrás)
    $oldDbPath = "$BaseDir\config\config.db"
    $newDbPath = "$DataDir\config.db"
    if ((Test-Path $oldDbPath) -and (-not (Test-Path $newDbPath))) {
        Write-Step "Migrando base de datos a nueva ubicación..."
        Copy-Item -Path $oldDbPath -Destination $newDbPath -Force
        Write-Ok "Base de datos migrada a: $DataDir"
    }
    
    Write-Ok "Directorio del programa: $InstallDir"
    Write-Ok "Directorio de datos: $DataDir (persiste entre actualizaciones)"
    
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
    Write-Host "  Ejecutable:  $InstallDir\$AppName\GestionPases.exe"
    Write-Host "  Datos:       $DataDir (PERSISTE entre actualizaciones)"
    Write-Host "  Browser:     $CacheDir (cache local)"
    Write-Host ""
    Write-Host "  Estructura de carpetas:"
    Write-Host "    $BaseDir\"
    Write-Host "    ├── app\       ← Se actualiza con cada release"
    Write-Host "    ├── data\      ← Tus configuraciones (se conservan)"
    Write-Host "    └── cache\     ← Browser Chromium"
    Write-Host ""
    Write-Host "  Puedes ejecutarlo desde:"
    Write-Host "  - El acceso directo en Menú Inicio/Escritorio"
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