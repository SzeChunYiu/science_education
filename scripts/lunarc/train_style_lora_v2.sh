#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua40
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -J train_lora
#SBATCH -o logs/train_lora_%j.out
#SBATCH -e logs/train_lora_%j.err

set +u
module load Anaconda3/2024.06-1
eval "$(conda shell.bash hook)"
conda activate /projects/hep/fs10/shared/nnbar/billy/packages/science_edu

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=/projects/hep/fs10/shared/nnbar/billy/packages/science_edu/lib/python3.11/site-packages:$BASE:$PYTHONPATH
export HF_HOME=/projects/hep/fs10/shared/nnbar/billy/.hf_cache
export HUGGINGFACE_HUB_CACHE=/projects/hep/fs10/shared/nnbar/billy/.hf_cache
export TRANSFORMERS_CACHE=/projects/hep/fs10/shared/nnbar/billy/.hf_cache
export TORCH_HOME=/projects/hep/fs10/shared/nnbar/billy/.torch_cache
mkdir -p /projects/hep/fs10/shared/nnbar/billy/.hf_cache /projects/hep/fs10/shared/nnbar/billy/.torch_cache
cd $BASE
mkdir -p logs models/style_learner

echo "=== Started: $(date) ==="
nvidia-smi | head -3

# Use diffusers official training script for SDXL LoRA
# First check if the script exists, otherwise download it
TRAIN_SCRIPT=/tmp/train_text_to_image_lora_sdxl.py
if [ ! -f "$TRAIN_SCRIPT" ]; then
    wget -q -O "$TRAIN_SCRIPT" "https://raw.githubusercontent.com/huggingface/diffusers/main/examples/text_to_image/train_text_to_image_lora_sdxl.py" 2>&1
fi

# Create metadata.jsonl for the dataset
python3 << 'PYEOF'
import json
from pathlib import Path
data_dir = Path("data/lora_training/teded_style")
entries = []
for img in sorted(data_dir.glob("*.png")):
    caption_file = img.with_suffix(".txt")
    caption = caption_file.read_text().strip() if caption_file.exists() else "teded_style educational illustration"
    entries.append({"file_name": img.name, "text": caption})
metadata_path = data_dir / "metadata.jsonl"
with open(metadata_path, "w") as f:
    for entry in entries:
        f.write(json.dumps(entry) + "\n")
print(f"Created metadata.jsonl with {len(entries)} entries")
PYEOF

echo "=== Starting LoRA Training ==="
accelerate launch --mixed_precision="fp16" "$TRAIN_SCRIPT" \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --train_data_dir="$BASE/data/lora_training/teded_style" \
  --output_dir="$BASE/models/style_learner/teded_style_lora" \
  --resolution=1024 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --num_train_epochs=20 \
  --learning_rate=1e-4 \
  --lr_scheduler="cosine" \
  --lr_warmup_steps=100 \
  --rank=32 \
  --mixed_precision="fp16" \
  --checkpointing_steps=1000 \
  --validation_prompt="teded_style, educational animated illustration of a scientist" \
  --validation_epochs=5 \
  --seed=42 \
  --caption_column="text" \
  --image_column="file_name" \
  --dataloader_num_workers=4 2>&1

echo "=== Training Complete: $(date) ==="
ls -lhR models/style_learner/teded_style_lora/ 2>/dev/null | head -20
