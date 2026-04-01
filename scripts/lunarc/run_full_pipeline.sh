#!/bin/bash
# Run the full LUNARC training pipeline for science education video production.
# Usage: bash scripts/lunarc/run_full_pipeline.sh [--test-mode]
#
# This submits SLURM jobs in sequence, waiting for each to complete before
# starting the next. Run from the LUNARC login node.

set -e

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
cd "$BASE"

TEST_FLAG=""
if [ "$1" = "--test-mode" ]; then
    TEST_FLAG="--test-mode"
    echo "=== RUNNING IN TEST MODE (3 videos only) ==="
fi

echo "=== Step 1: Feature Extraction ==="
JOB1=$(sbatch --parsable scripts/lunarc/extract_features.sh $TEST_FLAG)
echo "Submitted feature extraction job: $JOB1"
echo "Waiting for completion..."
srun --dependency=afterok:$JOB1 --time=00:01:00 echo "Feature extraction complete"

echo "=== Step 2: Train Style Models (4 MLPs) ==="
JOB2=$(sbatch --parsable scripts/lunarc/train_style_models.sh $TEST_FLAG)
echo "Submitted style model training job: $JOB2"
srun --dependency=afterok:$JOB2 --time=00:01:00 echo "Style models trained"

echo "=== Step 3: Train SDXL Style LoRA ==="
JOB3=$(sbatch --parsable scripts/lunarc/train_style_lora.sh)
echo "Submitted LoRA training job: $JOB3"
srun --dependency=afterok:$JOB3 --time=00:01:00 echo "Style LoRA trained"

echo "=== Step 4: Train Discriminators ==="
JOB4=$(sbatch --parsable scripts/lunarc/train_discriminators.sh)
echo "Submitted discriminator training job: $JOB4"
srun --dependency=afterok:$JOB4 --time=00:01:00 echo "Discriminators trained"

echo "=== Step 5: Train F5-TTS Voice ==="
JOB5=$(sbatch --parsable scripts/lunarc/train_voice.sh)
echo "Submitted voice training job: $JOB5"
srun --dependency=afterok:$JOB5 --time=00:01:00 echo "Voice trained"

echo ""
echo "=== ALL TRAINING COMPLETE ==="
echo "Models saved to: $BASE/models/"
echo ""
echo "Next steps:"
echo "  1. Sync models to local: bash scripts/lunarc/sync_models_local.sh"
echo "  2. Run batch narration: sbatch scripts/lunarc/batch_narration.sh"
