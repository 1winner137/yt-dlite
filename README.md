# YT-Dlite

**YT-Dlite** is a lightweight, versatile video/audio downloader that offers both a clean GUI and powerful command-line interface. Built on top of yt-dlp with simplicity in mind, and they works similarly in many ways.

![YT-Dlite Logo](https://github.com/1winner137/yt-dlite/blob/main/.github/yt-dlp.svg)

## Features

- **Dual Interface**: Use the intuitive GUI or efficient command-line interface
- **Format Options**: Download videos in mp4, webm, and other formats
- **Audio Extraction**: Extract audio in mp3, m4a, and more
- **Resume Support**: Continue interrupted downloads, especiall terminal mode
- **Format Listing**: View all available quality options before downloading
- **Custom Output**: Specify where to save your downloads
- **Safe Filenames**: Automatic sanitization of filenames
- **Dark and Light**: Themes for better user experience
- **PlayList Download** : Custom number suggest or Entire playlist download with easier
- **Verbosity** :  Supports ERROR, DEBUG, and INFO logging levels for better troubleshooting

## Installation

### Requirements

- Python 3.6+
- FFmpeg (required for format conversion and merging), but not MUST

### Quick Install

```bash
# Clone the repository
git clone https://github.com/1winner137/yt-dlite.git
cd yt-dlite

# Install dependencies
# For Non-Windows
chmod +x ./installation.sh

# For windows
Double click - installation.bat

# Install FFmpeg (platform specific)
# Windows: Download from https://ffmpeg.org/download.html and add to PATH
# macOS: brew install ffmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# Fedora: sudo dnf install ffmpeg
```

## Usage

### GUI Mode

Launch the graphical interface with:

```bash
python yt-dlite.py --gui
```
OR
```bash
python yt-dliteg.py
```

The GUI provides a simple interface for:
- Entering video/audio URLs
- Selecting output format
- Choosing download location
- Monitoring download progress
- Resuming interrupted downloads
- Freedom to choose formats

### Command-Line Interface

yt-dlite offers a powerful CLI for quick downloads and automation:

```bash
# Download video (default: mp4)
python yt-dlite.py --video https://www.youtube.com/watch?v=example

# Download audio (default: mp3)
python yt-dlite.py --audio https://www.youtube.com/watch?v=example

# Specify format
python yt-dlite.py --video https://www.youtube.com/watch?v=example --format webm

# Resume interrupted download
python yt-dlite.py --resume --video https://www.youtube.com/watch?v=example

# List all available formats
python yt-dlite.py --list-formats https://www.youtube.com/watch?v=example

# Specify output directory
python yt-dlite.py --video https://www.youtube.com/watch?v=example --output /path/to/save
```

## Advanced Usage

### Format Selection

List available formats:

```bash
python yt-dlite.py --list-formats https://www.youtube.com/watch?v=example
```

This will display all available formats with their IDs, extensions, and resolutions, not limited to site.

### Resume Downloads

yt-dlite can continue partially downloaded files:

```bash
python yt-dlite.py --resume --video https://www.youtube.com/watch?v=example
```

### Custom Output Directory

Save downloads to a specific location:

```bash
python yt-dlite.py --video https://www.youtube.com/watch?v=example --output ~/Downloads
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU GPLv3.0 License - see the LICENSE file for details.

## Acknowledgments

- Built on the excellent [yt-dlp](https://github.com/yt-dlp/yt-dlp) library
- Thanks to all contributors and users for suggestions and feedback

## Disclaimer

This tool is for personal use only. Please respect copyright laws and the YouTube Terms of Service. yt-dlite developers and contributors are not responsible for misuse of this software.
