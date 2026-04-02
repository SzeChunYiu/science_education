#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua40
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 8:00:00
#SBATCH -J extract_train
#SBATCH -o logs/extract_train_%j.out
#SBATCH -e logs/extract_train_%j.err

set +u
module load Anaconda3/2024.06-1 FFmpeg
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
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}'); import importlib.metadata; print(f'metadata: {importlib.metadata.version(\"torch\")}')"

echo "=== Feature Extraction ==="
python -m src.style_learner.feature_extraction.extract_all --device cuda 2>&1
echo "Features done: $(date)"

echo "=== Dataset Building ==="
python -c "
from src.style_learner.feature_extraction.dataset_builder import build_dataset, split_dataset
from pathlib import Path
ds = build_dataset(Path('data/style_reference/videos'))
splits = split_dataset(ds)
print(f'Dataset: {ds}, Splits: {splits}')
" 2>&1
echo "Dataset done: $(date)"

echo "=== Train Style MLPs ==="
python -m src.style_learner.training.train_all --device cuda 2>&1
echo "MLPs done: $(date)"

echo "=== Prepare Semantic + Flow Training Data ==="
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
ls -lh models/discriminators/ models/style_learner/
