# YT-Lite

**YT-Lite** is a lightweight, versatile YouTube downloader that offers both a clean GUI and powerful command-line interface. Built on top of yt-dlp with simplicity in mind, works in similar in many ways.
![YT-Lite Logo](https://github.com/1winner137/yt-lite/blob/main/.github/yt-dlp.svg)

## Features

- **Dual Interface**: Use the intuitive GUI or efficient command-line interface
- **Format Options**: Download videos in mp4, webm, and other formats
- **Audio Extraction**: Extract audio in mp3, m4a, and more
- **Resume Support**: Continue interrupted downloads, especiall terminal mode
- **Format Listing**: View all available quality options before downloading
- **Custom Output**: Specify where to save your downloads
- **Safe Filenames**: Automatic sanitization of filenames

## Installation

### Requirements

- Python 3.6+
- FFmpeg (required for format conversion and merging), but not MUST

### Quick Install

```bash
# Clone the repository
git clone https://github.com/1winner137/yt-lite.git
cd yt-lite

# Install dependencies
pip install -r requirements.txt

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
python yt-lite.py --gui
```

The GUI provides a simple interface for:
- Entering video/audio URLs
- Selecting output format
- Choosing download location
- Monitoring download progress
- Resuming interrupted downloads
- Freedom to choose formats

### Command-Line Interface

yt-lite offers a powerful CLI for quick downloads and automation:

```bash
# Download video (default: mp4)
python yt-lite.py --video https://www.youtube.com/watch?v=example

# Download audio (default: mp3)
python yt-lite.py --audio https://www.youtube.com/watch?v=example

# Specify format
python yt-lite.py --video https://www.youtube.com/watch?v=example --format webm

# Resume interrupted download
python yt-lite.py --resume --video https://www.youtube.com/watch?v=example

# List all available formats
python yt-lite.py --list-formats https://www.youtube.com/watch?v=example

# Specify output directory
python yt-lite.py --video https://www.youtube.com/watch?v=example --output /path/to/save
```

## Advanced Usage

### Format Selection

List available formats:

```bash
python yt-lite.py --list-formats https://www.youtube.com/watch?v=example
```

This will display all available formats with their IDs, extensions, and resolutions, not limited to site.

### Resume Downloads

yt-lite can continue partially downloaded files:

```bash
python yt-lite.py --resume --video https://www.youtube.com/watch?v=example
```

### Custom Output Directory

Save downloads to a specific location:

```bash
python yt-lite.py --video https://www.youtube.com/watch?v=example --output ~/Downloads
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

This tool is for personal use only. Please respect copyright laws and the YouTube Terms of Service. yt-lite developers are not responsible for misuse of this software.
