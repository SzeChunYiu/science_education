#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 1:00:00
#SBATCH -J train_style
#SBATCH -o logs/train_style_%j.out
#SBATCH -e logs/train_style_%j.err

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=$BASE
cd $BASE
mkdir -p logs

python -m src.style_learner.training.train_all "$@"
