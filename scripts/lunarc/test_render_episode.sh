#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua40
#SBATCH -t 02:00:00
#SBATCH -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH -J test_render
#SBATCH -o logs/test_render_%j.out
#SBATCH -e logs/test_render_%j.err

set -euo pipefail
echo "=== Test Episode Render ==="
echo "Job ID: $SLURM_JOB_ID, Node: $SLURMD_NODENAME"
echo "Start: $(date)"

set +u
module load Anaconda3/2024.06-1
module load FFmpeg/6.0
eval "$(conda shell.bash hook)"
conda activate /projects/hep/fs10/shared/nnbar/billy/packages/science_edu
set -u

# Cache dirs on project storage
BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=/projects/hep/fs10/shared/nnbar/billy/packages/science_edu/lib/python3.11/site-packages:$BASE:$PYTHONPATH
export HF_HOME=/projects/hep/fs10/shared/nnbar/billy/.hf_cache
export HUGGINGFACE_HUB_CACHE=/projects/hep/fs10/shared/nnbar/billy/.hf_cache
export TORCH_HOME=/projects/hep/fs10/shared/nnbar/billy/packages/.cache/torch
export XDG_CACHE_HOME=/projects/hep/fs10/shared/nnbar/billy/packages/.cache
export TMPDIR=/tmp

cd $BASE

SCRIPT="output/physics/01_classical_mechanics/01_newtons_laws/ep01_why_things_stop/scripts/ep01_youtube_long.md"
OUTPUT="output/physics/01_classical_mechanics/01_newtons_laws/ep01_why_things_stop/media/ep01_youtube_long.mp4"
WORKDIR="output/test_renders/ep01_work"

mkdir -p "$(dirname "$OUTPUT")" "$WORKDIR"

echo "Script: $SCRIPT"
echo "Output: $OUTPUT"
echo ""

python3 -c "
import sys, os
sys.path.insert(0, '.')
from src.pipeline.episode_renderer import render_episode

result = render_episode(
    script_path='$SCRIPT',
    output_mp4='$OUTPUT',
    aspect_ratio='16:9',
    fps=30,
    crf=23,
    work_dir='$WORKDIR',
    keep_work_dir=True,
    verbose=True,
)
print(f'Done: {result}')
"

echo ""
echo "=== Output file ==="
ls -lh "$OUTPUT" 2>/dev/null || echo "No output file!"
echo "=== Finished: $(date) ==="
