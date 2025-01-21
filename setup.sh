#!/bin/zsh
# Function to download and install Miniconda
install_miniconda() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
        bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
        bash Miniconda3-latest-MacOSX-x86_64.sh -b -p $HOME/miniconda3
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows (Cygwin, MinGW, or Git Bash)
        curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
        ./Miniconda3-latest-Windows-x86_64.exe /S /D=$HOME/miniconda3
    else
        echo "Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "conda could not be found, installing Miniconda..."
    install_miniconda
    # Initialize conda
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda init zsh
    # Reload the shell
    exec $SHELL
else
    echo "conda is already installed"
    # Initialize conda
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

# Create a new conda environment
conda create -y -n mewt python=3.9
source activate mewt
# The following installs need to be done in the given order
pip install uv
conda install -y cython
uv pip install cython
uv pip install librosa yt-dlp pyrubberband soundfile
# if [ ! -d "madmom" ]; then
#   git clone https://github.com/CPJKU/madmom.git
# fi
# cd madmom
# git submodule update --init --remote
# cd ..
uv pip install git+https://github.com/CPJKU/madmom
uv pip install "numpy<1.24"
conda install -y ffmpeg
uv pip install ffmpeg
uv pip install uvicorn fastapi pyaudio
if [ ! -d "demucs" ]; then
  git clone https://github.com/adefossez/demucs.git
fi
cd demucs
uv pip install .
cd ..

pip install BeatNet

