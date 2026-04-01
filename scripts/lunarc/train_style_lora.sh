#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 2:00:00
#SBATCH -J train_lora
#SBATCH -o logs/train_lora_%j.out
#SBATCH -e logs/train_lora_%j.err

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
cd $BASE
mkdir -p logs models/style_learner

# Prepare dataset
python -m src.style_learner.training.prepare_lora_dataset

# Train SDXL style LoRA using accelerate + kohya sd-scripts
accelerate launch --num_processes=1 --mixed_precision=fp16 \
  sdxl_train_network.py \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --train_data_dir="$BASE/data/lora_training/teded_style/" \
  --output_dir="$BASE/models/style_learner/" \
  --network_module=networks.lora \
  --network_dim=32 \
  --network_alpha=16 \
  --resolution=1024 \
  --train_batch_size=4 \
  --max_train_epochs=20 \
  --learning_rate=1e-4 \
  --mixed_precision=fp16 \
  --save_every_n_epochs=5 \
  --output_name="teded_style_v1" \
  --caption_extension=".txt" \
  --cache_latents \
  --optimizer_type="AdamW8bit"

echo "Style LoRA training complete"
