#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 2:00:00
#SBATCH -J narration
#SBATCH -o logs/narration_%A_%a.out
#SBATCH -e logs/narration_%A_%a.err
#SBATCH --array=0-188

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=$BASE
cd $BASE
mkdir -p logs output/assets/narration_clips

# Get episode list and select by array index
EPISODE=$(python -c "
import json
from pathlib import Path
index = json.loads(Path('output/episode_index.json').read_text())
print(index[$SLURM_ARRAY_TASK_ID]['script_path'])
")

python -c "
from src.audio.narration.f5_narrator import F5Narrator
narrator = F5Narrator(device='cuda')
narrator.load()
narrator.render_episode('$EPISODE')
narrator.unload()
"

echo "Narration complete for episode $SLURM_ARRAY_TASK_ID"
