#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 6:00:00
#SBATCH -J train_voice
#SBATCH -o logs/train_voice_%j.out
#SBATCH -e logs/train_voice_%j.err

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=$BASE
cd $BASE
mkdir -p logs models/style_learner/voice

# Prepare training data
python -c "
from src.audio.narration.voice_trainer import VoiceTrainer
from pathlib import Path
trainer = VoiceTrainer()
audio_files = list(Path('data/voice_reference/raw').glob('*.mp3'))
trainer.prepare_training_data(audio_files)
print('Training data prepared')
"

# Run F5-TTS fine-tuning
f5-tts_finetune \
  --dataset_dir data/voice_reference/prepared \
  --output_dir models/style_learner/voice \
  --epochs 100 \
  --batch_size 4 \
  --learning_rate 1e-5 \
  --save_every 20

echo "Voice training complete"
