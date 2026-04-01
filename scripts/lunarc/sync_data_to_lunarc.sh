#!/bin/bash
# Sync collected training data from local Mac to LUNARC.
# Run this LOCALLY after data collection completes.
#
# Usage: bash scripts/lunarc/sync_data_to_lunarc.sh

set -e

REMOTE="lunarc:/projects/hep/fs10/shared/nnbar/billy/science_education"
LOCAL="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Syncing data to LUNARC ==="

# Sync reference videos + frames
echo "Syncing style reference data..."
rsync -avz --progress \
    "$LOCAL/data/style_reference/" \
    "$REMOTE/data/style_reference/"

# Sync negative examples
echo "Syncing negative examples..."
rsync -avz --progress \
    "$LOCAL/data/style_negatives/" \
    "$REMOTE/data/style_negatives/"

# Sync voice reference audio
echo "Syncing voice reference..."
rsync -avz --progress \
    "$LOCAL/data/voice_reference/" \
    "$REMOTE/data/voice_reference/" \
    2>/dev/null || echo "No voice reference to sync"

# Sync LoRA training data
echo "Syncing LoRA training data..."
rsync -avz --progress \
    "$LOCAL/data/lora_training/" \
    "$REMOTE/data/lora_training/" \
    2>/dev/null || echo "No LoRA training data to sync"

# Sync source code
echo "Syncing source code..."
rsync -avz --progress \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='output/test_renders' \
    --exclude='*.mp4' \
    "$LOCAL/src/" \
    "$REMOTE/src/"

rsync -avz --progress \
    "$LOCAL/scripts/" \
    "$REMOTE/scripts/"

echo ""
echo "=== Data sync complete ==="
echo "Now SSH to LUNARC and run:"
echo "  bash scripts/lunarc/run_full_pipeline.sh"
