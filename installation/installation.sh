#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

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
    # Copy the CLI version
    cp ./yt-lite.py "$INSTALL_BIN_DIR/yt-lite.py"
    chmod +x "$INSTALL_BIN_DIR/yt-lite.py"
    
    # Copy the GUI version
    cp ./yt-liteg.py "$INSTALL_BIN_DIR/yt-liteg.py"
    chmod +x "$INSTALL_BIN_DIR/yt-liteg.py"
    
    echo -e "${GREEN}Python files copied successfully.${NC}"
}

# Function to create binaries and shortcuts
create_binaries_and_shortcuts() {
    echo "Creating binaries and shortcuts..."
    
    # Create binary for CLI version
    cat > "$INSTALL_BIN_DIR/yt-lite" << 'EOF'
#!/bin/bash
python3 "$(dirname "$0")/yt-lite.py" "$@"
EOF
    chmod +x "$INSTALL_BIN_DIR/yt-lite"
    
    # Create binary for GUI version
    cat > "$INSTALL_BIN_DIR/yt-liteg" << 'EOF'
#!/bin/bash
python3 "$(dirname "$0")/yt-liteg.py" "$@"
EOF
    chmod +x "$INSTALL_BIN_DIR/yt-liteg"
    
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
    
    # Create desktop entry for GUI version
    cat > "$DESKTOP_DIR/yt-liteg.desktop" << EOF
[Desktop Entry]
Type=Application
Name=YT-Lite GUI
Comment=YouTube Downloader GUI
Exec=$INSTALL_BIN_DIR/yt-liteg
Terminal=false
Categories=Utility;Network;
EOF
    
    echo -e "${GREEN}Desktop entry created at $DESKTOP_DIR/yt-liteg.desktop${NC}"
}

# Main function
main() {
    echo "Starting YT-Lite installation..."
    
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
    
    echo -e "${GREEN}YT-Lite installation completed successfully!${NC}"
    echo "You can now use 'yt-lite' for the command line version and 'yt-liteg' for the GUI version."
    
    if [ "$(id -u)" -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}Since you installed without administrator privileges:${NC}"
        echo "1. Make sure $INSTALL_BIN_DIR is in your PATH"
        echo "2. Run 'source ~/.bashrc' or restart your terminal"
    fi
}

# Run the main function
main
