#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# FFmpeg installation section
install_ffmpeg() {
    echo -e "${GREEN}FFmpeg Automatic Installer for Ubuntu/Linux${NC}"
    echo "=========================================="
    echo

    # Check if running as root for FFmpeg installation
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}FFmpeg installation requires root privileges.${NC}"
        echo "Please run this script with sudo or as root."
        echo "Skipping FFmpeg installation..."
        return 1
    fi

    # Function to check if a command exists
    command_exists() {
        command -v "$1" >/dev/null 2>&1
    }

    # Check if FFmpeg is already installed
    if command_exists ffmpeg; then
        echo -e "${GREEN}FFmpeg is already installed.${NC}"
        ffmpeg_version=$(ffmpeg -version | head -n 1)
        echo "Current version: $ffmpeg_version"
        return 0
    fi

    # Update repositories
    echo "Updating package lists..."
    apt-get update -qq

    # Install prerequisites
    echo "Installing prerequisites..."
    apt-get install -y -qq software-properties-common apt-transport-https ca-certificates curl

    # Add FFmpeg repository for the latest version
    echo "Adding FFmpeg repository..."
    add-apt-repository -y ppa:savoury1/ffmpeg4 >/dev/null 2>&1 || {
        echo -e "${YELLOW}Could not add FFmpeg repository. Trying default repository...${NC}"
    }
    apt-get update -qq

    # Install FFmpeg
    echo "Installing FFmpeg..."
    apt-get install -y -qq ffmpeg

    # Verify installation
    if command_exists ffmpeg; then
        echo
        echo -e "${GREEN}FFmpeg installation completed successfully!${NC}"
        echo "=========================================="
        ffmpeg_version=$(ffmpeg -version | head -n 1)
        echo "Installed version: $ffmpeg_version"
        echo
        echo "FFmpeg is now available in your system path."
    else
        echo -e "${YELLOW}Standard installation failed. Trying alternative method...${NC}"
        install_ffmpeg_from_source
    fi
}

# Alternative method if the standard FFmpeg installation fails
install_ffmpeg_from_source() {
    echo "Repository installation failed. Trying direct installation..."
    
    # Install build dependencies
    apt-get install -y -qq build-essential yasm cmake libtool libc6 libc6-dev unzip wget
    
    # Create a temporary directory
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    
    # Download and extract FFmpeg
    echo "Downloading FFmpeg source..."
    wget -q https://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
    echo "Extracting source files..."
    tar xjf ffmpeg-snapshot.tar.bz2
    cd ffmpeg
    
    # Configure and build
    echo "Configuring and building FFmpeg (this may take a while)..."
    ./configure --enable-gpl --enable-nonfree --disable-debug --enable-shared
    make -j$(nproc)
    make install
    ldconfig
    
    # Clean up
    cd /
    rm -rf "$TMP_DIR"
    
    if command_exists ffmpeg; then
        echo -e "${GREEN}FFmpeg installed successfully from source.${NC}"
        ffmpeg_version=$(ffmpeg -version | head -n 1)
        echo "Installed version: $ffmpeg_version"
    else
        echo -e "${RED}Installation from source failed.${NC}"
        return 1
    fi
}

# Function to check if running as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${YELLOW}WARNING: This script is not running with administrator privileges.${NC}"
        echo "Some features may not work properly."
        echo "It's recommended to run this script with sudo or as root."
        echo ""
        echo -e "${YELLOW}Do you want to continue with limited installation? (y/n)${NC}"
        read -r response
        if [[ "$response" != "y" && "$response" != "Y" ]]; then
            echo "Installation aborted."
            exit 1
        fi
        
        # Set installation paths for non-root user
        INSTALL_BIN_DIR="$HOME/.local/bin"
        mkdir -p "$INSTALL_BIN_DIR"
        
        # Check if ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo -e "${YELLOW}Adding $INSTALL_BIN_DIR to your PATH...${NC}"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo 'Please run "source ~/.bashrc" after installation or restart your terminal.'
        fi
    else
        # Set installation paths for root user
        INSTALL_BIN_DIR="/usr/local/bin"
    fi
    
    echo "Installation directory: $INSTALL_BIN_DIR"
}

# Function to install required Python packages
install_requirements() {
    echo "Installing required Python packages..."
    
    if [ "$(id -u)" -ne 0 ]; then
        pip3 install --user argparse yt-dlp || {
            echo "Failed to install Python packages with pip3. Trying pip..."
            pip install --user argparse yt-dlp || {
                echo "Failed to install with regular pip. Trying with --break-system-packages..."
                pip3 install --user --break-system-packages argparse yt-dlp || {
                    pip install --user --break-system-packages argparse yt-dlp || {
                        echo -e "${RED}Failed to install Python packages. Please make sure pip is installed.${NC}"
                        exit 1
                    }
                }
            }
        }
    else
        pip3 install argparse yt-dlp || {
            echo "Failed to install Python packages with pip3. Trying pip..."
            pip install argparse yt-dlp || {
                echo "Failed to install with regular pip. Trying with --break-system-packages..."
                pip3 install --break-system-packages argparse yt-dlp || {
                    pip install --break-system-packages argparse yt-dlp || {
                        echo -e "${RED}Failed to install Python packages. Please make sure pip is installed.${NC}"
                        exit 1
                    }
                }
            }
        }
    fi
    
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

# Function to create binaries and shortcuts
create_binaries_and_shortcuts() {
    echo "Creating binaries and shortcuts..."
    
    # Create binary for CLI version with new name
    cat > "$INSTALL_BIN_DIR/yt-dlite4terminal" << 'EOF'
#!/bin/bash
python3 "$(dirname "$0")/yt-dlitex.py" "$@"
EOF
    chmod +x "$INSTALL_BIN_DIR/yt-dlite4terminal"
    
    # Create binary for GUI version with new name
    cat > "$INSTALL_BIN_DIR/yt-dlite" << 'EOF'
#!/bin/bash
python3 "$(dirname "$0")/yt-dlite.py" "$@"
EOF
    chmod +x "$INSTALL_BIN_DIR/yt-dlite"
    
    echo -e "${GREEN}Binaries and shortcuts created successfully.${NC}"
}

# Function to create desktop entries (for GUI version)
create_desktop_entries() {
    if [ "$(id -u)" -ne 0 ]; then
        DESKTOP_DIR="$HOME/.local/share/applications"
    else
        DESKTOP_DIR="/usr/share/applications"
    fi
    
    mkdir -p "$DESKTOP_DIR"
    
    # Create desktop entry for GUI version with new name
    cat > "$DESKTOP_DIR/yt-dlite.desktop" << EOF
[Desktop Entry]
Type=Application
Name=YT-DLite
Comment=YouTube Downloader
Exec=$INSTALL_BIN_DIR/yt-dlite
Terminal=false
Categories=Utility;Network;
EOF
    
    echo -e "${GREEN}Desktop entry created at $DESKTOP_DIR/yt-dlite.desktop${NC}"
}

# Main function
main() {
    echo -e "${GREEN}Starting YT-DLite installation...${NC}"
    
    # Install FFmpeg if running as root
    if [ "$(id -u)" -eq 0 ]; then
        install_ffmpeg
    else
        echo -e "${YELLOW}Skipping FFmpeg installation as script is not running as root.${NC}"
        echo "Please run 'sudo apt-get install ffmpeg' manually if FFmpeg is not installed."
    fi
    
    # Check for root access and setup paths
    check_root
    
    # Install required packages
    install_requirements
    
    # Copy Python files
    copy_files
    
    # Create shortcuts and binaries
    create_binaries_and_shortcuts
    
    # Create desktop entries for GUI
    create_desktop_entries
    
    echo -e "${GREEN}YT-DLite installation completed successfully!${NC}"
    echo "You can now use 'yt-dlite4terminal' for the command line version and 'yt-dlite' for the GUI version."
    
    if [ "$(id -u)" -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}Since you installed without administrator privileges:${NC}"
        echo "1. Make sure $INSTALL_BIN_DIR is in your PATH"
        echo "2. Run 'source ~/.bashrc' or restart your terminal"
    fi
}

# Run the main function
main
