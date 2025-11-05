# Build script for SpotiSync
# Run with: .\build.ps1

Write-Host "Building SpotiSync..." -ForegroundColor Cyan

# Check if yt-dlp.exe exists
$ytdlp_found = Test-Path "yt-dlp.exe"
$ffmpeg_found = Test-Path "ffmpeg.exe"

if (-not $ytdlp_found) {
    Write-Host "WARNING: yt-dlp.exe not found!" -ForegroundColor Yellow
    Write-Host "Download from: https://github.com/yt-dlp/yt-dlp/releases" -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne "y") {
        exit
    }
} else {
    Write-Host "✓ yt-dlp.exe found" -ForegroundColor Green
}

if (-not $ffmpeg_found) {
    Write-Host "WARNING: ffmpeg.exe not found!" -ForegroundColor Yellow
    Write-Host "This is optional but recommended for better audio quality" -ForegroundColor Yellow
    Write-Host "Download from: https://ffmpeg.org/download.html" -ForegroundColor Yellow
    $response = Read-Host "Continue without ffmpeg? (y/n)"
    if ($response -ne "y") {
        exit
    }
} else {
    Write-Host "✓ ffmpeg.exe found" -ForegroundColor Green
}

# Update spec file to include found binaries
Write-Host "`nUpdating build configuration..." -ForegroundColor Cyan
$specContent = Get-Content "SpotiSync.spec" -Raw

if ($ytdlp_found -or $ffmpeg_found) {
    $binaries = @()
    if ($ytdlp_found) {
        $binaries += "        ('yt-dlp.exe', '.'),"
    }
    if ($ffmpeg_found) {
        $binaries += "        ('ffmpeg.exe', '.'),"
    }
    
    $binaryString = $binaries -join "`n"
    
    # Replace the binaries section
    $specContent = $specContent -replace "(?s)binaries=\[.*?\]", "binaries=[`n$binaryString`n    ]"
    Set-Content "SpotiSync.spec" $specContent
    
    Write-Host "✓ Binaries configured in spec file" -ForegroundColor Green
}

# Clean previous builds
if (Test-Path "dist") {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force dist
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force build
}

# Build the EXE
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
pyinstaller SpotiSync.spec

# Check if build succeeded
if (Test-Path "dist\SpotiSync.exe") {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "EXE location: dist\SpotiSync.exe" -ForegroundColor Green
    
    # Open dist folder
    $open = Read-Host "`nOpen dist folder? (y/n)"
    if ($open -eq "y") {
        Start-Process "dist"
    }
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
    Write-Host "Check the output above for errors." -ForegroundColor Red
}
