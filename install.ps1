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
    # 1. Verificar/Instalar Python (solo la primera vez)
    # Verificar si python funciona realmente (no es solo un alias del Microsoft Store)
    $pythonWorks = $false
    try {
        $result = python --version 2>&1
        if ($result -match "Python 3\.") {
            $pythonWorks = $true
            Write-Ok "Python ya instalado: $result"
        }
    } catch {}
    
    if (-not $pythonWorks) {
        Write-Step "Primera instalación: instalando Python..."
        Write-Warn "Esto descargará ~30MB solo la primera vez"
        
        $tempDir = "$env:TEMP\GestionPases_install"
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        
        # Descargar Python
        Write-Step "Descargando Python..."
        $pythonUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
        $pythonInstaller = "$tempDir\python.exe"
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing -TimeoutSec 300
        
        # Instalar silenciosamente
        Write-Step "Instalando Python..."
        Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        
        # Recargar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Ok "Python instalado"
    }
    
    # 2. Verificar/Instalar browser Chromium (solo la primera vez)
    # Buscar si ya existe algún chromium instalado
    $existingChrome = Get-ChildItem -Path $CacheDir -Recurse -Filter "chrome.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if (-not $existingChrome) {
        Write-Step "Primera instalación: configurando browser Chromium..."
        Write-Warn "Esto descargará ~400MB solo la primera vez"
        Write-Host "  Cache: $CacheDir" -ForegroundColor Gray
        
        # Crear directorios
        New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
        $tempDir = "$env:TEMP\GestionPases_browser"
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        
        # Descargar browser - usar la URL más reciente
        Write-Step "Descargando Chromium (~400MB)..."
        $browserUrl = "https://playwright.azureedge.net/builds/chromium/1155/chromium-win64.zip"
        $browserZip = "$tempDir\chromium.zip"
        Write-Host "  URL: $browserUrl" -ForegroundColor Gray
        Write-Host "  Destino: $browserZip" -ForegroundColor Gray
        
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $browserUrl -OutFile $browserZip -UseBasicParsing
        $ProgressPreference = 'Continue'
        
        if (Test-Path $browserZip) {
            $zipSize = [math]::Round((Get-Item $browserZip).Length / 1MB, 1)
            Write-Ok "Descarga completada: ${zipSize}MB"
            
            # Extraer a carpeta de cache
            Write-Step "Instalando browser en cache..."
            Expand-Archive -Path $browserZip -DestinationPath $CacheDir -Force
            Remove-Item $browserZip -Force
            Write-Ok "Extracción completada"
        } else {
            Write-Error "El archivo ZIP no se descargó correctamente"
        }
        
        # Limpiar
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        
        # Verificar si se instaló
        $existingChrome = Get-ChildItem -Path $CacheDir -Recurse -Filter "chrome.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($existingChrome) {
            Write-Ok "Browser instalado en: $($existingChrome.DirectoryName)"
        } else {
            Write-Warn "Browser no encontrado en: $CacheDir"
            Write-Host "  Contenido de cache:" -ForegroundColor Gray
            Get-ChildItem $CacheDir -Recurse -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $($_.FullName)" -ForegroundColor Gray }
        }
    } else {
        Write-Ok "Browser Chromium ya instalado en cache"
        Write-Host "  Ubicación: $($existingChrome.FullName)" -ForegroundColor Gray
    }
    
    # 3. Obtener última release
    Write-Step "Buscando última versión..."
    $release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
    $version = $release.tag_name
    $asset = $release.assets | Where-Object { $_.name -like "*$AppName*.zip" } | Select-Object -First 1
    
    if (-not $asset) {
        Write-Error "No se encontró el archivo $AppName.zip en la release $version"
        exit 1
    }
    
    Write-Ok "Versión encontrada: $version"
    
    # 4. Crear directorios necesarios
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
    
    # 5. Descargar (sin Chromium - solo exe + dependencias Python)
    Write-Step "Descargando $AppName v$version ($([math]::Round($asset.size/1MB, 1)) MB)..."
    $zipPath = "$env:TEMP\$AppName.zip"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing
    Write-Ok "Descarga completada"
    
    # 6. Extraer
    Write-Step "Extrayendo archivos..."
    Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
    Remove-Item $zipPath -Force
    Write-Ok "Archivos extraídos"
    
    # 7. Crear shortcuts
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
    
    # 8. Resumen
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