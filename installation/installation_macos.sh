#!/bin/bash
# macOS Installation Script (installation_macos.sh)

echo "===== YT-DLite Installation for macOS ====="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed."
    echo "Please install Python from https://www.python.org/downloads/"
    echo "Or download the precompiled version from:"
    echo "https://github.com/1winner137/yt-dlite/releases"
    exit 1
fi

# Install yt-dlp
echo "Installing yt-dlp..."
pip3 install -U yt-dlp --break-system-packages

# Check for Homebrew (needed for ffmpeg)
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew (needed for ffmpeg)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ $? -ne 0 ]; then
        echo "Failed to install Homebrew. You may need to install ffmpeg manually."
        echo "Visit https://ffmpeg.org/download.html for more information,"
        echo "or use the precompiled version from:"
        echo "https://github.com/1winner137/yt-dlite/releases"
    fi
fi

# Check and install ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg not found. Installing ffmpeg..."
    brew install ffmpeg
    if [ $? -ne 0 ]; then
        echo "Failed to install ffmpeg. Some features may not work."
        echo "You can download the precompiled version from:"
        echo "https://github.com/1winner137/yt-dlite/releases"
    fi
fi

# Check for required files
echo "Checking for required files..."
for file in yt-dlite.py yt-dlitec.py misc.py; do
    if [ ! -f "$file" ]; then
        echo "ERROR: $file not found in the current directory."
        echo "This file is required for yt-dlite to function properly."
        exit 1
    fi
done

# Create executable wrappers
echo "Creating executable wrappers for YT-DLite..."
cat > yt-dlite << EOL
#!/bin/bash
cd "$(dirname "\$0")"
python3 "./yt-dlite.py" "\$@"
EOL

cat > yt-dlitec << EOL
#!/bin/bash
cd "$(dirname "\$0")"
python3 "./yt-dlitec.py" "\$@"
EOL

chmod +x yt-dlite
chmod +x yt-dlitec

# Ask user about system-wide installation
read -p "Would you like to install yt-dlite system-wide for all users? (y/n): " system_wide

if [[ $system_wide == "y" || $system_wide == "Y" ]]; then
    echo "Installing system-wide..."
    sudo mkdir -p /usr/local/share/yt-dlite
    sudo cp yt-dlite.py yt-dlitec.py misc.py /usr/local/share/yt-dlite/
    
    # Create system-wide wrappers
    cat > system-yt-dlite << EOL
#!/bin/bash
cd /usr/local/share/yt-dlite
python3 ./yt-dlite.py "\$@"
EOL

    cat > system-yt-dlitec << EOL
#!/bin/bash
cd /usr/local/share/yt-dlite
python3 ./yt-dlitec.py "\$@"
EOL

    sudo mv system-yt-dlite /usr/local/bin/yt-dlite
    sudo mv system-yt-dlitec /usr/local/bin/yt-dlitec
    sudo chmod +x /usr/local/bin/yt-dlite
    sudo chmod +x /usr/local/bin/yt-dlitec
    
    echo "YT-DLite installed system-wide. You can now run yt-dlite or yt-dlitec from any directory."
else
    # Ask if user wants it in their local PATH
    read -p "Would you like to add yt-dlite to your personal PATH? (y/n): " add_to_path
    
    if [[ $add_to_path == "y" || $add_to_path == "Y" ]]; then
        mkdir -p ~/.local/share/yt-dlite
        cp yt-dlite.py yt-dlitec.py misc.py ~/.local/share/yt-dlite/
        
        # Create personal wrappers
        cat > personal-yt-dlite << EOL
#!/bin/bash
cd $HOME/.local/share/yt-dlite
python3 ./yt-dlite.py "\$@"
EOL

        cat > personal-yt-dlitec << EOL
#!/bin/bash
cd $HOME/.local/share/yt-dlite
python3 ./yt-dlitec.py "\$@"
EOL

        mkdir -p ~/.local/bin
        mv personal-yt-dlite ~/.local/bin/yt-dlite
        mv personal-yt-dlitec ~/.local/bin/yt-dlitec
        chmod +x ~/.local/bin/yt-dlite
        chmod +x ~/.local/bin/yt-dlitec
        
        # Add to PATH in both zsh and bash profiles
        shell_updated=false
        for profile in ~/.zshrc ~/.bash_profile; do
            if [ -f "$profile" ]; then
                if ! grep -q "PATH=\"\$HOME/.local/bin:\$PATH\"" "$profile"; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
                    shell_updated=true
                fi
            fi
        done
        
        if [ "$shell_updated" = true ]; then
            echo "PATH has been updated in your shell profiles."
            echo "Please restart your terminal or source your profile."
        fi
        
        echo "YT-DLite executables added to ~/.local/bin"
    fi
fi

echo "Installation completed successfully!"
echo "----------------------------------------"
echo "You can now run:"
echo "  - ./yt-dlite for the GUI version"
echo "  - ./yt-dlitec for the terminal version"

if [[ $system_wide == "y" || $system_wide == "Y" || $add_to_path == "y" || $add_to_path == "Y" ]]; then
    echo "Or after restarting your terminal:"
    echo "  - yt-dlite for the GUI version"
    echo "  - yt-dlitec for the terminal version"
fi

echo "If you encounter any issues, check the precompiled version at:"
echo "https://github.com/1winner137/yt-dlite/releases"
