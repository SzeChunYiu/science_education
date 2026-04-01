#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -J train_disc
#SBATCH -o logs/train_disc_%j.out
#SBATCH -e logs/train_disc_%j.err

BASE=/projects/hep/fs10/shared/nnbar/billy/science_education
export PYTHONPATH=$BASE
cd $BASE
mkdir -p logs models/discriminators

# Prepare training data
python -c "from src.quality.discriminators.prepare_training_data import prepare_all; prepare_all()"

# Train all discriminators
python -c "
from src.quality.discriminators.style_discriminator import StyleDiscriminator
from src.quality.discriminators.semantic_discriminator import SemanticDiscriminator
from src.quality.discriminators.flow_discriminator import FlowDiscriminator

print('Training style discriminator...')
sd = StyleDiscriminator(device='cuda')
sd.train('data/discriminator_training/style_data.pt', 'models/discriminators/style_discriminator.pt')

print('Training semantic discriminator...')
sem = SemanticDiscriminator(device='cuda')
sem.train('data/discriminator_training/semantic_pairs.jsonl', 'models/discriminators/semantic_discriminator.pt')

print('Training flow discriminator...')
fd = FlowDiscriminator(device='cuda')
fd.train('data/discriminator_training/flow_pairs.jsonl', 'models/discriminators/flow_discriminator.pt')

print('All discriminators trained.')
"
