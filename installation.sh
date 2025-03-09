#!/bin/bash

# Function to check if running as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script needs to be run as administrator."
        echo "Please run with sudo or as root."
        exit 1
    fi
}

# Function to install required Python packages
install_requirements() {
    echo "Installing required Python packages..."
    pip3 install argparse yt-dlp tkinter || {
        echo "Failed to install Python packages with pip3. Trying pip..."
        pip install argparse yt-dlp tkinter || {
            echo "Failed to install Python packages. Please make sure pip is installed."
            exit 1
        }
    }
    echo "Required Python packages installed successfully."
}

# Function to create directories if they don't exist
create_directories() {
    echo "Creating necessary directories..."
    mkdir -p /usr/local/bin
    echo "Directories created successfully."
}

# Function to copy Python files to /usr/local/bin
copy_files() {
    echo "Copying Python files..."
    
    # Assuming the Python files are withiin the current downloaded directory
    # Copy the CLI version
    cp ./yt-lite.py /usr/local/bin/yt-lite.py
    chmod +x /usr/local/bin/yt-lite.py
    
    # Copy the GUI version
    cp ./yt-liteg.py /usr/local/bin/yt-liteg.py
    chmod +x /usr/local/bin/yt-liteg.py
    
    echo "Python files copied successfully."
}

# Function to create shortcuts
create_shortcuts() {
    echo "Creating shortcuts..."
    
    # Create shortcut for CLI version
    cat > /usr/local/bin/yt-lite << 'EOF'
#!/bin/bash
python3 /usr/local/bin/yt-lite.py "$@"
EOF
    chmod +x /usr/local/bin/yt-lite
    
    # Create shortcut for GUI version
    cat > /usr/local/bin/yt-liteg << 'EOF'
#!/bin/bash
python3 /usr/local/bin/yt-liteg.py "$@"
EOF
    chmod +x /usr/local/bin/yt-liteg
    
    echo "Shortcuts created successfully."
}

# Main function
main() {
    echo "Starting YT-Lite installation..."
    
    # Check for root access
    check_root
    
    # Install required packages
    install_requirements
    
    # Create necessary directories
    create_directories
    
    # Copy Python files
    copy_files
    
    # Create shortcuts
    create_shortcuts
    
    echo "YT-Lite installation completed successfully!"
    echo "You can now use 'yt-lite' for the command line version and 'yt-liteg' for the GUI version."
}

# Run the main function
main
