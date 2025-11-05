# SpotiSync - Quick Start Guide

## For End Users (Using the EXE)

### First Time Setup

1. **Download SpotiSync.exe**
2. **Double-click to run** - Windows may show a security warning (click "More info" → "Run anyway")
3. **Welcome screen** will guide you through the basics

### How to Use

**Step 1: Get Your Music List**
- Click **"Get CSV..."** → Opens Exportify website
- Log in to Spotify and export your playlist
- Download the CSV file

**OR**

- Click **"Create CSV..."** → Type song names (one per line)
- Save the file

**Step 2: Select the CSV**
- Click **"Browse..."** next to CSV File
- Select your downloaded/created CSV

**Step 3: Choose Output Folder**
- Default: Your Downloads folder
- Click **"Browse..."** to change
- Click **"Open Folder"** to see downloaded files

**Step 4: Start Downloading**
- Click **"Start Download"**
- Watch the progress bar and stats
- Click **"Cancel"** if you want to stop

### Understanding the Interface

**Progress Display:**
- **✓** = Successfully downloaded
- **✗** = Failed to download
- **⊘** = Skipped (already exists)

**Color Codes:**
- 🟢 Green = Success
- 🔴 Red = Error
- 🟡 Yellow = Warning
- 🔵 Blue = Info

**Options Explained:**

- **Format**: Audio file type (mp3 recommended)
- **Threads**: Download 2-4 songs at once (more = faster but heavier)
- **Archive File**: Tracks what you've downloaded (prevents duplicates)
- **If file exists**: 
  - Skip = Don't download again (default)
  - Overwrite = Download and replace

### Tips & Tricks

✅ **First download taking long?** This is normal, yt-dlp needs to initialize
✅ **Some songs fail?** They might not be on YouTube or are region-locked
✅ **Want to resume later?** Use the archive file feature
✅ **Downloaded to wrong folder?** Check the Output path before starting
✅ **App not responding?** Don't panic, downloads continue in background

### Common Questions

**Q: Do I need Spotify Premium?**
A: No! You just need to export your playlist via Exportify

**Q: Where does the music come from?**
A: YouTube - the app searches YouTube for each track

**Q: Can I download entire playlists?**
A: Yes! Export from Exportify and select the CSV

**Q: Will this work offline?**
A: No, you need internet to download from YouTube

**Q: How do I get better audio quality?**
A: Use "m4a" or "opus" format instead of mp3. Make sure ffmpeg is bundled with the app.

**Q: What is ffmpeg?**
A: A tool that converts audio/video. It's bundled with SpotiSync for better quality downloads.

**Q: Can I use this on Mac/Linux?**
A: Currently Windows only (EXE), but Python source works on all platforms

### Troubleshooting

**"yt-dlp not found"**
→ The EXE should include it. Try redownloading the app.

**"ffmpeg not found" (warning)**
→ Optional but recommended for best quality
→ The app will still work but audio conversion may be limited

**"No track name column found"**
→ Your CSV needs a column called "Track Name"
→ Use "Create CSV..." for a simple list

**Downloads are very slow**
→ Set Threads to 1 or 2
→ Check your internet connection

**Window freezes during download**
→ This is normal! Check the status log for progress
→ The UI updates every few seconds

**Files aren't in the output folder**
→ Click "Open Folder" to verify the location
→ Check if downloads actually succeeded (green ✓)

### Settings

Your preferences are saved automatically:
- Last used format
- Thread count
- Output folder
- Archive file location

Settings location: `%APPDATA%\SpotiSync\settings.json`

---

**Need more help?**
Click **Help → Help & Guide** in the menu for detailed instructions!

Enjoy your music! 🎵
