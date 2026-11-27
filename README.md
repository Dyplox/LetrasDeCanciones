# 🎵 File Renamer - Automation with Claude API

Automatically rename image and PDF files using Claude's vision and document understanding capabilities. Perfect for organizing musical scores, sheet music, or any document collection.

## Purpose

Built to organize the digital music folder of **Alma Viajera**, the duo of my uncle Jorge Eliecer and Don Abelardo. They photograph the lyrics of their songs with a phone, and every photo ends up with the device's auto-generated name. This script reads each photo with Claude, takes the song title and renames the file with it, so the whole repertoire stays sorted alphabetically and any song is easy to find.

> 🇪🇸 **Propósito:** ordenar la carpeta digital de música de *Alma Viajera*, el dueto de mi tío Jorge Eliecer y Don Abelardo. Las fotos de las letras de sus canciones llegan con el nombre que les pone el celular; el script lee cada foto con IA, toma el título de la canción y renombra el archivo con él, para tener todos sus temas ordenados alfabéticamente.

## Features

✅ **Automated Title Extraction** - Uses Claude API to intelligently extract titles from documents  
✅ **Smart Sanitization** - Converts names to Title Case with spaces, removes accents and special characters  
✅ **UUID-Only Processing** - Automatically skips manually named files, only processes iPhone auto-generated names (UUID format)  
✅ **Cost Optimization** - Avoids unnecessary API calls for already-named files  
✅ **Robust Error Handling** - Continues processing even if individual files fail  
✅ **Clear Logging** - Progress updates and comprehensive error messages  
✅ **Filesystem Safe** - Handles name conflicts and filesystem limitations automatically  

## Supported Formats

- **Images**: `.jpg`, `.jpeg`, `.png`
- **Documents**: `.pdf`

## Prerequisites

- Python 3.8 or higher
- An Anthropic API key (get it from https://console.anthropic.com/account/keys)

## Installation

### 1. Clone or Download This Project

```bash
cd ~/Documents/Claude/Projects/LetrasDeCanciones
```

### 2. Create Virtual Environment (Recommended)

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

**Option A: Using .env file (Recommended)**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# For macOS/Linux
nano .env
# OR
vim .env

# For Windows
# Use Notepad or any text editor to open .env
```

Add your API key:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
INPUT_FOLDER_PATH=./input_files
```

**Option B: Using Environment Variable**

```bash
# macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## Usage

### 1. Prepare Your Files

The `input_files` folder already exists in the repo (it is git-ignored, so your photos and documents are never committed). Add your files to it:

```bash
# Copy your PDF and image files into input_files/
cp ~/Downloads/song_title.pdf input_files/
cp ~/Downloads/sheet_music.jpg input_files/
```

### 2. Run the Script

**From Terminal/Command Line:**

```bash
# macOS/Linux
python script_renamer.py

# Windows
python script_renamer.py
```

**From IDE:**

**VSCode:**
- Open the project folder in VSCode
- Open `script_renamer.py`
- Click "Run" button (▶) in top right, or press `Ctrl+F5`

**PyCharm:**
- Open the project in PyCharm
- Right-click on `script_renamer.py`
- Select "Run 'script_renamer'"

**Jupyter Notebook:**
```python
exec(open('script_renamer.py').read())
```

### 3. Check Results

The script will output detailed progress:

```
==================================================
FILE RENAMING AUTOMATION - STARTING
==================================================

Found 54 file(s) to process

Skipping: My Photo.jpeg (not auto-generated UUID)
Skipping: song_title.pdf (not auto-generated UUID)

Processing: 9375781E-BE30-4EBB-92A4-C1CD2D56ED2B.jpeg
  ℹ Compressed image by 45.2%
  ✓ Renamed: 9375781E-BE30-4EBB-92A4-C1CD2D56ED2B.jpeg → La vida es bella.jpeg

Processing: CF5678F0-AF98-43FF-B013-A19D92968B45.jpeg
  ✓ Renamed: CF5678F0-AF98-43FF-B013-A19D92968B45.jpeg → Melodia nocturna.jpeg

==================================================
SUMMARY
==================================================
Skipped (non-UUID): 52
Total processed: 2
Successful: 2
Errors: 0
Time elapsed: 8.23s
==================================================
```

Your renamed files will be in the same `input_files/` folder.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | - | Your Anthropic API key |
| `INPUT_FOLDER_PATH` | ❌ No | `./input_files` | Folder containing files to rename |

### Script Options

Edit the top of `script_renamer.py` to customize:

```python
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}  # File types to process
MAX_FILENAME_LENGTH = 255  # Filesystem limit (don't change unless needed)
```

## How It Works

1. **File Discovery**: Scans the input folder for supported file types
2. **UUID Filter**: Only processes files with iPhone auto-generated UUID names (e.g., `9375781E-BE30-4EBB-92A4-C1CD2D56ED2B.jpeg`)
   - ✅ Processes: `9375781E-BE30-4EBB-92A4-C1CD2D56ED2B.jpeg`
   - ⏭️ Skips: `My Photo.jpeg`, `song_title.pdf`, `image_1.jpg`
   - This saves API costs by avoiding files that are already named
2. **API Upload**: Sends each file to Claude using the Files API
3. **Title Extraction**: Claude (Sonnet 4.6) analyzes the document and extracts the main title
4. **Sanitization**: Converts the title to a filesystem-safe name:
   - Removes accents: `café` → `cafe`
   - Converts to Title Case: `My Song` → `My Song`
   - Preserves spaces between words
   - Removes special characters: `Song (remix)!` → `Song Remix`
5. **Renaming**: Renames the original file, preserving its extension
6. **Conflict Resolution**: If a file with that name exists, adds a suffix: `_1`, `_2`, etc.

## Error Handling

The script handles various error scenarios gracefully:

| Error | Handling |
|-------|----------|
| **API Quota Exceeded** | Logs error and continues with next file |
| **Corrupted File** | Skips file, logs error, continues |
| **Invalid Filename** | Uses fallback name "Unnamed" |
| **File Already Exists** | Adds numeric suffix automatically |
| **Missing API Key** | Shows clear error message and exits |

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

Make sure your `.env` file exists in the project root and contains:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Or set the environment variable:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### "No valid files found"

Check that:
- Files are in the correct folder (default: `./input_files/`)
- Files have supported extensions (`.pdf`, `.jpg`, `.jpeg`, `.png`)
- Files are not hidden (don't start with a dot)

### "Could not extract title from file"

This might happen if:
- The file is corrupted
- The file has no identifiable title (blank page, image, etc.)
- The file format is not fully readable by Claude

The script will use the fallback name "Unnamed" in these cases. You can manually rename it afterward.

### API Rate Limit

If you get rate limit errors:
- The script will skip the current file and continue
- Wait a few minutes before running again
- Check your API usage at https://console.anthropic.com/account/usage

## Performance Tips

- Process files in batches if you have many files
- Use images with clear, readable text for best results
- Ensure PDFs are not image-based scans without OCR (Claude works better with searchable PDFs)

## Security Notes

⚠️ **Important**: 
- Never commit `.env` file to version control (it's in `.gitignore`)
- Never share your API key publicly
- Keep your `ANTHROPIC_API_KEY` confidential
- Use environment variables in production systems

## Development & Advanced Use

### Custom Sanitization

Edit the `sanitize_filename()` method in `script_renamer.py` to customize name processing.

Example transformations:
- `la_vida_es_bella` → `La vida es bella` (Title Case with spaces)
- `café montaña` → `Cafe Montana` (accents removed)
- `song (remix)!` → `Song Remix` (special characters removed)

### Process All Files (Disable UUID Filter)

By default, the script only processes files with iPhone auto-generated UUID names to save API costs. If you want to process ALL files regardless of name:

Edit `script_renamer.py` and comment out the UUID check:

```python
# Skip files that don't have UUID-style names (iPhone naming pattern)
# if not self._is_uuid_filename(file_path.stem):
#     print(f"Skipping: {file_path.name} (not auto-generated UUID)")
#     self.skipped_files += 1
#     continue
```

### Change Claude Model

Edit `script_renamer.py` to use a different Claude model:

```python
message = self.client.messages.create(
    model="claude-sonnet-4-6",  # Change to: claude-opus-4-7, claude-haiku-4-5-20251001
    max_tokens=200,
    ...
)
```

Available models:
- `claude-sonnet-4-6` (fast, balanced, recommended) ⭐
- `claude-opus-4-7` (most capable, but slower and more expensive)
- `claude-haiku-4-5-20251001` (fastest, economical)

### Batch Processing

To process multiple folders:

```python
folders = ["./input_files", "./documents", "./images"]
for folder in folders:
    renamer = FileRenamer(API_KEY, folder)
    renamer.process_files()
```

### Integration with Other Tools

The script can be imported as a module:

```python
from script_renamer import FileRenamer

renamer = FileRenamer(api_key="sk-ant-...", input_folder="./my_files")
renamer.process_files()
```

## Support & Feedback

For issues or questions:
- Check the Troubleshooting section above
- Review your API key configuration
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## License

This script uses the Anthropic Python SDK. See LICENSE for details.

---

**Happy renaming!** 🎉
