# Download Required Binaries for SpotiSync
# Run with: .\download_binaries.ps1

Write-Host "SpotiSync - Binary Downloader" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check if yt-dlp.exe exists
if (Test-Path "yt-dlp.exe") {
    Write-Host "✓ yt-dlp.exe already exists" -ForegroundColor Green
    $update_ytdlp = Read-Host "Do you want to update it? (y/n)"
    if ($update_ytdlp -ne "y") {
        $download_ytdlp = $false
    } else {
        $download_ytdlp = $true
    }
} else {
    Write-Host "✗ yt-dlp.exe not found" -ForegroundColor Yellow
    $download_ytdlp = $true
}

# Check if ffmpeg.exe exists
if (Test-Path "ffmpeg.exe") {
    Write-Host "✓ ffmpeg.exe already exists" -ForegroundColor Green
    $update_ffmpeg = Read-Host "Do you want to update it? (y/n)"
    if ($update_ffmpeg -ne "y") {
        $download_ffmpeg = $false
    } else {
        $download_ffmpeg = $true
    }
} else {
    Write-Host "✗ ffmpeg.exe not found" -ForegroundColor Yellow
    $download_ffmpeg = $true
}

# Download yt-dlp
if ($download_ytdlp) {
    Write-Host "`nDownloading yt-dlp.exe..." -ForegroundColor Cyan
    try {
        $ytdlp_url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        Invoke-WebRequest -Uri $ytdlp_url -OutFile "yt-dlp.exe"
        Write-Host "✓ yt-dlp.exe downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to download yt-dlp.exe" -ForegroundColor Red
        Write-Host "Please download manually from: https://github.com/yt-dlp/yt-dlp/releases" -ForegroundColor Yellow
    }
}

# Download ffmpeg (more complex as it's in a zip)
if ($download_ffmpeg) {
    Write-Host "`nNote: ffmpeg requires manual download" -ForegroundColor Yellow
    Write-Host "Please follow these steps:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://github.com/BtbN/FFmpeg-Builds/releases" -ForegroundColor Cyan
    Write-Host "2. Download: ffmpeg-master-latest-win64-gpl.zip" -ForegroundColor Cyan
    Write-Host "3. Extract: bin/ffmpeg.exe from the archive" -ForegroundColor Cyan
    Write-Host "4. Place ffmpeg.exe in this folder" -ForegroundColor Cyan
    
    $open_browser = Read-Host "`nOpen download page in browser? (y/n)"
    if ($open_browser -eq "y") {
        Start-Process "https://github.com/BtbN/FFmpeg-Builds/releases"
    }
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Download Summary:" -ForegroundColor Cyan

if (Test-Path "yt-dlp.exe") {
    Write-Host "✓ yt-dlp.exe: Ready" -ForegroundColor Green
} else {
    Write-Host "✗ yt-dlp.exe: Missing (REQUIRED)" -ForegroundColor Red
}

if (Test-Path "ffmpeg.exe") {
    Write-Host "✓ ffmpeg.exe: Ready" -ForegroundColor Green
} else {
    Write-Host "⚠ ffmpeg.exe: Missing (Recommended)" -ForegroundColor Yellow
}

Write-Host "`nOnce you have both files, run: .\build.ps1" -ForegroundColor Cyan
