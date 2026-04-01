#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 1:00:00
#SBATCH -J char_lora
#SBATCH -o logs/char_lora_%j.out
#SBATCH -e logs/char_lora_%j.err

CHARACTER=${1:?"Usage: sbatch train_character_lora.sh <character_name>"}
BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
cd $BASE
mkdir -p logs models/style_learner/characters

accelerate launch --num_processes=1 --mixed_precision=fp16 \
  sdxl_train_network.py \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --train_data_dir="$BASE/data/lora_training/character_${CHARACTER}/" \
  --output_dir="$BASE/models/style_learner/characters/" \
  --network_module=networks.lora \
  --network_dim=16 \
  --network_alpha=8 \
  --resolution=1024 \
  --train_batch_size=2 \
  --max_train_epochs=30 \
  --learning_rate=1e-4 \
  --mixed_precision=fp16 \
  --save_every_n_epochs=10 \
  --output_name="${CHARACTER}_v1" \
  --caption_extension=".txt" \
  --cache_latents

echo "Character LoRA training complete for: $CHARACTER"
