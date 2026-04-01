#!/bin/bash
# Sync trained models from LUNARC to local Mac mini.
# Run this LOCALLY (not on LUNARC).
#
# Usage: bash scripts/lunarc/sync_models_local.sh

set -e

REMOTE="lunarc:/projects/hep/fs10/shared/nnbar/billy/science_education"
LOCAL="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Syncing models from LUNARC to local ==="
echo "Remote: $REMOTE"
echo "Local:  $LOCAL"

# Sync style learner models (LoRAs, MLPs)
echo "Syncing style learner models..."
rsync -avz --progress \
    "$REMOTE/models/style_learner/" \
    "$LOCAL/models/style_learner/"

# Sync discriminator models
echo "Syncing discriminator models..."
rsync -avz --progress \
    "$REMOTE/models/discriminators/" \
    "$LOCAL/models/discriminators/"

# Sync pre-rendered narration (if any)
echo "Syncing narration clips..."
rsync -avz --progress \
    "$REMOTE/output/assets/narration_clips/" \
    "$LOCAL/output/assets/narration_clips/" \
    2>/dev/null || echo "No narration clips to sync"

# Sync dataset stats for reference
echo "Syncing dataset report..."
rsync -avz --progress \
    "$REMOTE/data/style_reference/dataset/" \
    "$LOCAL/data/style_reference/dataset/" \
    2>/dev/null || echo "No dataset to sync"

echo ""
echo "=== Sync complete ==="
echo "Models size:"
du -sh "$LOCAL/models/"
echo ""
echo "Ready to run local inference pipeline."
