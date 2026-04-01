#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -J feature_extract
#SBATCH -o logs/features_%j.out
#SBATCH -e logs/features_%j.err

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=$BASE
cd $BASE

# Activate conda environment
source activate style_learner 2>/dev/null || conda activate style_learner 2>/dev/null

# Create logs directory if needed
mkdir -p logs

# Report environment
echo "=== Environment ==="
echo "Date: $(date)"
echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Python: $(python --version)"
echo "PyTorch: $(python -c 'import torch; print(torch.__version__)' 2>/dev/null)"
echo "CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null)"
echo "==================="

python -m src.style_learner.feature_extraction.extract_all "$@"
