#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua40
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -J build_train
#SBATCH -o logs/build_train_%j.out
#SBATCH -e logs/build_train_%j.err

# Skip slow feature extraction steps (camera motion, text layout, quality, narration)
# CLIP features are already extracted for all 332 videos
# Focus on: dataset building -> MLP training -> discriminator training

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

echo "=== Started: $(date) ==="
nvidia-smi | head -3
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# Verify CLIP features exist
CLIP_COUNT=$(find data/style_reference/videos -name "features.json" | wc -l)
echo "CLIP features: $CLIP_COUNT/332 videos"

echo "=== Dataset Building ==="
python -c "
from src.style_learner.feature_extraction.dataset_builder import build_dataset, split_dataset, generate_report
from pathlib import Path
ds = build_dataset(Path('data/style_reference/videos'))
splits = split_dataset(ds)
report = generate_report(ds, splits)
print(report)
" 2>&1
echo "Dataset done: $(date)"

echo "=== Train Style MLPs ==="
python -m src.style_learner.training.train_all --device cuda 2>&1
echo "MLPs done: $(date)"

echo "=== Prepare Discriminator Training Data ==="
python -c "
from src.quality.discriminators.prepare_training_data import prepare_all
prepare_all()
" 2>&1
echo "Data prep done: $(date)"

echo "=== Train Semantic Discriminator ==="
python -c "
from src.quality.discriminators.semantic_discriminator import SemanticDiscriminator
sem = SemanticDiscriminator(device='cuda')
sem.train('data/discriminator_training/semantic_pairs.jsonl', 'models/discriminators/semantic_discriminator.pt')
" 2>&1
echo "Semantic disc done: $(date)"

echo "=== Train Flow Discriminator ==="
python -c "
from src.quality.discriminators.flow_discriminator import FlowDiscriminator
fd = FlowDiscriminator(device='cuda')
fd.train('data/discriminator_training/flow_pairs.jsonl', 'models/discriminators/flow_discriminator.pt')
" 2>&1
echo "Flow disc done: $(date)"

echo "=== ALL COMPLETE: $(date) ==="
echo "Models:"
ls -lh models/discriminators/ 2>/dev/null
ls -lh models/style_learner/ 2>/dev/null
echo "Datasets:"
ls -lh data/style_learner/ 2>/dev/null
ls -lh data/style_reference/videos/dataset.jsonl 2>/dev/null
