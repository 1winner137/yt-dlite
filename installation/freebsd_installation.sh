#!/bin/sh
# FreeBSD Installation Script (installation.sh)

echo "===== YT-DLite Installation for FreeBSD ====="

# Check for Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python is not installed."
    echo "Please install Python with: sudo pkg install python3 py39-pip"
    echo "Or download the precompiled version from:"
    echo "https://github.com/1winner137/yt-dlite/releases"
    exit 1
fi

# Install yt-dlp
echo "Installing yt-dlp..."
pip3 install -U yt-dlp --break-system-packages

# Check for ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg not found. Installing ffmpeg..."
    sudo pkg update
    sudo pkg install -y ffmpeg
    if [ $? -ne 0 ]; then
        echo "Failed to install ffmpeg. Some features may not work."
        echo "You can manually install ffmpeg or use the precompiled version from:"
        echo "https://github.com/1winner137/yt-dlite/releases"
    fi
fi

# Check for required files
echo "Checking for required files..."
for file in ../yt-dlite.py ../yt-dlitec.py ../misc.py; do
    if [ ! -f "$file" ]; then
        echo "ERROR: $(basename "$file") not found in the parent directory."
        echo "This file is required for yt-dlite to function properly."
        exit 1
    fi
done

# Create executable wrappers
echo "Creating executable wrappers for YT-DLite..."
cat > yt-dlite << 'EOL'
#!/bin/sh
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
python3 "$SCRIPT_DIR/../yt-dlite.py" "$@"
EOL

cat > yt-dlitec << 'EOL'
#!/bin/sh
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
python3 "$SCRIPT_DIR/../yt-dlitec.py" "$@"
EOL

chmod +x yt-dlite
chmod +x yt-dlitec

# Ask user about system-wide installation
printf "Would you like to install yt-dlite system-wide for all users? (y/n): "
read system_wide

if [ "$system_wide" = "y" ] || [ "$system_wide" = "Y" ]; then
    echo "Installing system-wide..."
    sudo mkdir -p /usr/local/share/yt-dlite
    sudo cp ../yt-dlite.py ../yt-dlitec.py ../misc.py /usr/local/share/yt-dlite/
    
    # Create system-wide wrappers
    cat > system-yt-dlite << 'EOL'
#!/bin/sh
cd /usr/local/share/yt-dlite
python3 ./yt-dlite.py "$@"
EOL

    cat > system-yt-dlitec << 'EOL'
#!/bin/sh
cd /usr/local/share/yt-dlite
python3 ./yt-dlitec.py "$@"
EOL

    sudo mv system-yt-dlite /usr/local/bin/yt-dlite
    sudo mv system-yt-dlitec /usr/local/bin/yt-dlitec
    sudo chmod +x /usr/local/bin/yt-dlite
    sudo chmod +x /usr/local/bin/yt-dlitec
    
    echo "YT-DLite installed system-wide. You can now run yt-dlite or yt-dlitec from any directory."
else
    # Ask if user wants it in their local PATH
    printf "Would you like to add yt-dlite to your personal PATH? (y/n): "
    read add_to_path
    
    if [ "$add_to_path" = "y" ] || [ "$add_to_path" = "Y" ]; then
        mkdir -p ~/.local/share/yt-dlite
        cp ../yt-dlite.py ../yt-dlitec.py ../misc.py ~/.local/share/yt-dlite/
        
        # Create personal wrappers
        cat > personal-yt-dlite << 'EOL'
#!/bin/sh
cd $HOME/.local/share/yt-dlite
python3 ./yt-dlite.py "$@"
EOL

        cat > personal-yt-dlitec << 'EOL'
#!/bin/sh
cd $HOME/.local/share/yt-dlite
python3 ./yt-dlitec.py "$@"
EOL

        mkdir -p ~/.local/bin
        mv personal-yt-dlite ~/.local/bin/yt-dlite
        mv personal-yt-dlitec ~/.local/bin/yt-dlitec
        chmod +x ~/.local/bin/yt-dlite
        chmod +x ~/.local/bin/yt-dlitec
        
        # Check if ~/.local/bin is in PATH
        case ":$PATH:" in
            *":$HOME/.local/bin:"*) 
                echo "~/.local/bin is already in PATH."
                ;;
            *)
                # Check which shell configuration file to use
                if [ -n "$ZSH_VERSION" ]; then
                    shell_config="~/.zshrc"
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
                elif [ -n "$BASH_VERSION" ]; then
                    shell_config="~/.bashrc"
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
                else
                    # Default to .profile for other shells
                    shell_config="~/.profile"
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.profile
                fi
                echo "Added ~/.local/bin to PATH in $shell_config"
                echo "Please restart your terminal or run 'source $shell_config'"
                ;;
        esac
        
        echo "YT-DLite executables added to ~/.local/bin"
    fi
fi

echo "Installation completed successfully!"
echo "----------------------------------------"
echo "You can now run:"
echo "  - ./yt-dlite for the GUI version"
echo "  - ./yt-dlitec for the terminal version"

if [ "$system_wide" = "y" ] || [ "$system_wide" = "Y" ] || [ "$add_to_path" = "y" ] || [ "$add_to_path" = "Y" ]; then
    echo "Or after restarting your terminal:"
    echo "  - yt-dlite for the GUI version"
    echo "  - yt-dlitec for the terminal version"
fi

echo "If you encounter any issues, report it on github account."
echo "You can check the precompiled version at: https://github.com/1winner137/yt-dlite/releases"