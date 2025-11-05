# Building SpotiSync EXE - Step by Step Guide

## Quick Start (3 Steps)

1. **Get the binaries:**
   ```powershell
   .\download_binaries.ps1
   ```

2. **Build the EXE:**
   ```powershell
   .\build.ps1
   ```

3. **Find your EXE:**
   - Located in `dist\SpotiSync.exe`

---

## Detailed Instructions

### Step 1: Install Python and Dependencies

1. **Install Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation

2. **Install required packages:**
   ```powershell
   pip install -r requirements.txt
   ```

### Step 2: Download Required Binaries

#### Option A: Automated (Recommended)
```powershell
.\download_binaries.ps1
```
This will download yt-dlp.exe automatically and guide you to ffmpeg.

#### Option B: Manual Download

**yt-dlp.exe (Required):**
1. Visit: https://github.com/yt-dlp/yt-dlp/releases
2. Download: `yt-dlp.exe` from the latest release
3. Place it in the SpotiSync folder (same folder as SpotiSync.py)

**ffmpeg.exe (Recommended):**
1. Visit: https://github.com/BtbN/FFmpeg-Builds/releases
2. Download: `ffmpeg-master-latest-win64-gpl.zip`
3. Extract the archive
4. Navigate to: `bin\ffmpeg.exe` inside the extracted folder
5. Copy `ffmpeg.exe` to the SpotiSync folder

### Step 3: Build the EXE

**Automated Build:**
```powershell
.\build.ps1
```

The build script will:
- ✅ Check for yt-dlp.exe and ffmpeg.exe
- ✅ Update the build configuration automatically
- ✅ Run PyInstaller
- ✅ Show build results

**Manual Build:**
```powershell
pyinstaller SpotiSync.spec
```

### Step 4: Test the EXE

1. Navigate to `dist\SpotiSync.exe`
2. Double-click to run
3. You should see:
   - Welcome dialog (first run)
   - Main window with all features
   - Status messages showing yt-dlp and ffmpeg are found

### Step 5: Distribute

Your EXE is now ready to share! It includes:
- ✅ SpotiSync application
- ✅ yt-dlp.exe (bundled)
- ✅ ffmpeg.exe (bundled)
- ✅ All required Python libraries

Users can simply download and run `SpotiSync.exe` - no installation needed!

---

## Troubleshooting

### Build Errors

**"PyInstaller not found"**
```powershell
pip install pyinstaller
```

**"sv_ttk not found"**
```powershell
pip install sv-ttk
```

**"yt-dlp.exe not found" during build**
- Make sure yt-dlp.exe is in the same folder as SpotiSync.py
- Run `.\download_binaries.ps1` to download it

**"ffmpeg.exe not found" warning**
- This is optional but recommended
- The app will build without it, but audio quality may be limited
- Download from the link in Step 2

### Testing Issues

**EXE won't run on other computers**
- Build with: `--onefile` flag (already set in spec file)
- Make sure you built for the correct architecture (64-bit recommended)

**"yt-dlp not found" when running EXE**
- Rebuild with binaries properly configured
- Check that SpotiSync.spec includes yt-dlp.exe in binaries section

**Audio conversion fails**
- ffmpeg.exe was not bundled
- Rebuild with ffmpeg.exe in the project folder

### Clean Build

If you need to rebuild from scratch:

```powershell
# Remove old builds
Remove-Item -Recurse -Force dist, build
Remove-Item SpotiSync.spec

# Regenerate spec file (or use the provided one)
pyinstaller --onefile --noconsole SpotiSync.py

# Edit SpotiSync.spec to add binaries (or use build.ps1)
.\build.ps1
```

---

## Advanced Options

### Custom Icon

1. Get an `.ico` file (256x256 recommended)
2. Save it as `icon.ico` in the project folder
3. Edit `SpotiSync.spec`:
   ```python
   icon='icon.ico'
   ```
4. Rebuild

### Smaller EXE Size

The EXE will be large (~80-100 MB) because it includes:
- Python runtime
- yt-dlp.exe (~10 MB)
- ffmpeg.exe (~70 MB)

To reduce size:
- Remove ffmpeg.exe from the bundle (not recommended)
- Use UPX compression (already enabled in spec file)

### Creating an Installer

Use **Inno Setup** (free):
1. Download: https://jrsoftware.org/isinfo.php
2. Create a script to package SpotiSync.exe
3. Build installer.exe

Example Inno Setup script (save as `installer.iss`):
```
[Setup]
AppName=SpotiSync
AppVersion=1.0
DefaultDirName={pf}\SpotiSync
DefaultGroupName=SpotiSync
OutputDir=installer
OutputBaseFilename=SpotiSync_Setup

[Files]
Source: "dist\SpotiSync.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\SpotiSync"; Filename: "{app}\SpotiSync.exe"
```

---

## File Structure

After building, you should have:

```
SpotiSync/
├── SpotiSync.py          (Source code)
├── SpotiSync.spec        (Build configuration)
├── build.ps1             (Build script)
├── download_binaries.ps1 (Binary downloader)
├── requirements.txt      (Python dependencies)
├── yt-dlp.exe           (Required binary)
├── ffmpeg.exe           (Recommended binary)
├── build/               (Temporary build files)
├── dist/
│   └── SpotiSync.exe    (Your final EXE!)
└── docs/
    ├── README.md
    └── QUICKSTART.md    (User guide)

```

---

## Next Steps

✅ **Built successfully?** Share the EXE from `dist\SpotiSync.exe`

✅ **Want to customize?** Edit `SpotiSync.py` and rebuild

✅ **Ready to release?** See `DISTRIBUTION.md` for release checklist

✅ **Need help?** Check the documentation or open an issue

---

**Happy building! 🎵**
