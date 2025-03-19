#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Homebrew if not already installed
install_homebrew() {
    if ! command_exists brew; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH based on processor architecture
        if [[ $(uname -m) == "arm64" ]]; then
            # For Apple Silicon
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            # For Intel Mac
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        echo -e "${GREEN}Homebrew installed successfully.${NC}"
    else
        echo "Homebrew is already installed."
    fi
}

# Function to install FFmpeg using Homebrew
install_ffmpeg() {
    echo -e "${GREEN}FFmpeg Installer for macOS${NC}"
    echo "=========================================="
    echo
    
    # Check if FFmpeg is already installed
    if command_exists ffmpeg; then
        echo -e "${GREEN}FFmpeg is already installed.${NC}"
        ffmpeg_version=$(ffmpeg -version | head -n 1)
        echo "Current version: $ffmpeg_version"
        return 0
    fi
    
    # Install FFmpeg using Homebrew
    echo "Installing FFmpeg..."
    brew install ffmpeg
    
    # Verify installation
    if command_exists ffmpeg; then
        echo -e "${GREEN}FFmpeg installation completed successfully!${NC}"
        echo "=========================================="
        ffmpeg_version=$(ffmpeg -version | head -n 1)
        echo "Installed version: $ffmpeg_version"
        echo
        echo "FFmpeg is now available in your system path."
        return 0
    else
        echo -e "${RED}Failed to install FFmpeg. Please check for errors.${NC}"
        return 1
    fi
}

# Function to set up installation paths
setup_paths() {
    # macOS doesn't have root vs non-root installation like Linux
    # We'll use ~/Applications for user-specific installation
    INSTALL_BIN_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_BIN_DIR"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}Adding $INSTALL_BIN_DIR to your PATH...${NC}"
        # Check if using bash or zsh
        if [[ "$SHELL" == */zsh ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
            echo 'Please run "source ~/.zshrc" after installation or restart your terminal.'
        else
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bash_profile"
            echo 'Please run "source ~/.bash_profile" after installation or restart your terminal.'
        fi
    fi
    
    echo "Installation directory: $INSTALL_BIN_DIR"
}

# Function to install required Python packages
install_requirements() {
    echo "Installing required Python packages..."
    
    # Check if pip is installed
    if ! command_exists pip3; then
        echo "Installing pip3..."
        brew install python3
    fi
    
    pip3 install argparse yt-dlp || {
        echo "Failed to install Python packages with pip3. Trying pip..."
        pip install argparse yt-dlp || {
            echo -e "${RED}Failed to install Python packages. Please make sure pip is installed.${NC}"
            exit 1
        }
    }
    
    echo -e "${GREEN}Required Python packages installed successfully.${NC}"
}

# Function to copy Python files to installation directory
copy_files() {
    echo "Copying Python files..."
    
    # Assuming the Python files are in the current directory
    # Copy with new filenames as requested
    if [ -f "./yt-lite.py" ]; then
        cp ./yt-lite.py "$INSTALL_BIN_DIR/yt-dlitex.py"
        chmod +x "$INSTALL_BIN_DIR/yt-dlitex.py"
    else
        echo -e "${YELLOW}Warning: yt-lite.py not found in current directory.${NC}"
        echo "Creating an empty file. Please replace it with the actual content later."
        touch "$INSTALL_BIN_DIR/yt-dlitex.py"
        chmod +x "$INSTALL_BIN_DIR/yt-dlitex.py"
    fi
    
    if [ -f "./yt-liteg.py" ]; then
        cp ./yt-liteg.py "$INSTALL_BIN_DIR/yt-dlite.py"
        chmod +x "$INSTALL_BIN_DIR/yt-dlite.py"
    else
        echo -e "${YELLOW}Warning: yt-liteg.py not found in current directory.${NC}"
        echo "Creating an empty file. Please replace it with the actual content later."
        touch "$INSTALL_BIN_DIR/yt-dlite.py"
        chmod +x "$INSTALL_BIN_DIR/yt-dlite.py"
    fi
    
    echo -e "${GREEN}Python files copied successfully.${NC}"
}

# Function to create executable scripts
create_executables() {
    echo "Creating executable scripts..."
    
    # Create script for CLI version with new name
    cat > "$INSTALL_BIN_DIR/yt-dlite4cmd" << 'EOF'
#!/bin/bash
python3 "$(dirname "$0")/yt-dlitex.py" "$@"
EOF
    chmod +x "$INSTALL_BIN_DIR/yt-dlite4cmd"
    
    # Create script for GUI version with new name
    cat > "$INSTALL_BIN_DIR/yt-dlite" << 'EOF'
#!/bin/bash
python3 "$(dirname "$0")/yt-dlite.py" "$@"
EOF
    chmod +x "$INSTALL_BIN_DIR/yt-dlite"
    
    echo -e "${GREEN}Executable scripts created successfully.${NC}"
}

# Function to create macOS application bundle
create_app_bundle() {
    echo "Creating macOS application bundle..."
    
    # Create Applications directory if it doesn't exist
    APP_DIR="$HOME/Applications"
    mkdir -p "$APP_DIR"
    
    # Create the application bundle structure
    APP_BUNDLE="$APP_DIR/YT-DLite.app"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    mkdir -p "$APP_BUNDLE/Contents/Resources"
    
    # Create the Info.plist file
    cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>YT-DLite</string>
    <key>CFBundleIdentifier</key>
    <string>com.yt-dlite.app</string>
    <key>CFBundleName</key>
    <string>YT-DLite</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF
    
    # Create the executable script
    cat > "$APP_BUNDLE/Contents/MacOS/YT-DLite" << EOF
#!/bin/bash
python3 "$INSTALL_BIN_DIR/yt-dlite.py" "\$@"
EOF
    chmod +x "$APP_BUNDLE/Contents/MacOS/YT-DLite"
    
    echo -e "${GREEN}macOS application bundle created at $APP_BUNDLE${NC}"
}

# Main function
main() {
    echo -e "${GREEN}Starting YT-DLite installation for macOS...${NC}"
    
    # Install Homebrew (package manager for macOS)
    install_homebrew
    
    # Install FFmpeg using Homebrew
    install_ffmpeg
    
    # Setup installation paths
    setup_paths
    
    # Install required packages
    install_requirements
    
    # Copy Python files
    copy_files
    
    # Create executable scripts
    create_executables
    
    # Create macOS application bundle
    create_app_bundle
    
    echo -e "${GREEN}YT-DLite installation completed successfully!${NC}"
    echo "You can now use 'yt-dlite4cmd' for the command line version and 'yt-dlite' for the GUI version."
    echo "The GUI version is also available as an application in your Applications folder."
    echo ""
    echo -e "${YELLOW}Note: If the commands are not found, please run:${NC}"
    if [[ "$SHELL" == */zsh ]]; then
        echo "source ~/.zshrc"
    else
        echo "source ~/.bash_profile"
    fi
    echo "Or restart your terminal."
}

# Run the main function
main
