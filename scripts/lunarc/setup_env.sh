#!/bin/bash
# Setup ML environment on LUNARC Cosmos for science education pipeline
# Run once: bash scripts/lunarc/setup_env.sh

set -e

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
ENV_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/style_learner

echo "=== Setting up style learner environment on LUNARC ==="

# Load Anaconda
module load Anaconda3/2024.06-1

# Create conda environment
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating conda environment at $ENV_DIR..."
    conda create -p "$ENV_DIR" python=3.11 -c conda-forge -y
else
    echo "Environment already exists at $ENV_DIR"
fi

# Activate
source activate "$ENV_DIR"

# Install PyTorch with CUDA
echo "Installing PyTorch with CUDA..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies
echo "Installing training dependencies..."
pip install accelerate transformers diffusers safetensors
pip install sentence-transformers
pip install tensorboard

# Install data collection tools
echo "Installing data collection tools..."
pip install yt-dlp
pip install "scenedetect[opencv]"
pip install openai-whisper
pip install easyocr

# Install quality scoring
pip install simple-aesthetics-predictor
pip install ultralytics

# Install TTS
pip install f5-tts

# Install audio
pip install audiocraft librosa

# Install utilities
pip install colorthief Pillow numpy tqdm pyyaml spacy textstat
pip install python-Levenshtein

# Download spaCy model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p "$BASE/logs"
mkdir -p "$BASE/models/style_learner/characters"
mkdir -p "$BASE/models/discriminators"
mkdir -p "$BASE/data/style_reference"
mkdir -p "$BASE/data/style_negatives"
mkdir -p "$BASE/data/discriminator_training/rejected_scenes"
mkdir -p "$BASE/data/lora_training"
mkdir -p "$BASE/output/assets/narration_clips"
mkdir -p "$BASE/output/assets/equation_clips"

echo "=== Environment setup complete ==="
echo "Activate with: source activate $ENV_DIR"
echo "Test with: python -c 'import torch; print(f\"CUDA: {torch.cuda.is_available()}\")'"
