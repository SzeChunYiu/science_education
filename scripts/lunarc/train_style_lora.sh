#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua40
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -J train_lora
#SBATCH -o logs/train_lora_%j.out
#SBATCH -e logs/train_lora_%j.err

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
mkdir -p logs models/style_learner data/lora_training/teded_style

echo "=== Started: $(date) ==="
nvidia-smi | head -3
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# Dataset is already prepared (200 keyframes in data/lora_training/teded_style/)
echo "=== Training SDXL LoRA with corrected loop ==="

python3 << 'TRAINEOF'
import torch
import json
import logging
from pathlib import Path
from diffusers import StableDiffusionXLPipeline, DDPMScheduler, AutoencoderKL
from peft import LoraConfig, get_peft_model
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from torchvision import transforms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoraImageDataset(Dataset):
    def __init__(self, data_dir, resolution=1024):
        self.data_dir = Path(data_dir)
        self.images = sorted(self.data_dir.glob("*.png"))
        self.transform = transforms.Compose([
            transforms.Resize((resolution, resolution)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ])
        self.resolution = resolution

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        caption_path = img_path.with_suffix(".txt")
        image = Image.open(img_path).convert("RGB")
        caption = caption_path.read_text().strip() if caption_path.exists() else "teded_style educational illustration"
        return {"image": self.transform(image), "caption": caption}


# Load pipeline components separately for better control
logger.info("Loading SDXL base model...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
)

noise_scheduler = DDPMScheduler.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", subfolder="scheduler"
)

# Configure LoRA on UNet only
lora_config = LoraConfig(
    r=32,
    lora_alpha=16,
    target_modules=["to_k", "to_q", "to_v", "to_out.0"],
    lora_dropout=0.05,
)

pipe.unet = get_peft_model(pipe.unet, lora_config)
pipe.unet.to("cuda", dtype=torch.float32)  # Train in fp32 to avoid NaN
pipe.unet.train()

# Freeze VAE and text encoders
pipe.vae.requires_grad_(False)
pipe.text_encoder.requires_grad_(False)
pipe.text_encoder_2.requires_grad_(False)
pipe.vae.to("cuda", dtype=torch.float16)
pipe.text_encoder.to("cuda", dtype=torch.float16)
pipe.text_encoder_2.to("cuda", dtype=torch.float16)

# Dataset
dataset = LoraImageDataset("data/lora_training/teded_style", resolution=1024)
dataloader = DataLoader(dataset, batch_size=1, shuffle=True, num_workers=2)
logger.info(f"Dataset: {len(dataset)} images")

# Optimizer
trainable_params = [p for p in pipe.unet.parameters() if p.requires_grad]
logger.info(f"Trainable params: {sum(p.numel() for p in trainable_params):,}")
optimizer = torch.optim.AdamW(trainable_params, lr=1e-4, weight_decay=0.01)

# Training
num_epochs = 20
resolution = 1024

logger.info(f"Starting training for {num_epochs} epochs...")

for epoch in range(num_epochs):
    total_loss = 0.0
    num_steps = 0
    for step, batch in enumerate(dataloader):
        images = batch["image"].to("cuda", dtype=torch.float16)
        captions = batch["caption"]

        # Encode images to latents
        with torch.no_grad():
            latents = pipe.vae.encode(images).latent_dist.sample()
            latents = latents * pipe.vae.config.scaling_factor
            latents = latents.to(dtype=torch.float32)

        # Encode text prompts
        with torch.no_grad():
            prompt_embeds_tuple = pipe.encode_prompt(
                prompt=captions,
                device="cuda",
                num_images_per_prompt=1,
                do_classifier_free_guidance=False,
            )
            # encode_prompt returns (prompt_embeds, negative_prompt_embeds, pooled_prompt_embeds, negative_pooled_prompt_embeds)
            prompt_embeds = prompt_embeds_tuple[0].to(dtype=torch.float32)
            pooled_prompt_embeds = prompt_embeds_tuple[2].to(dtype=torch.float32)

        # Generate proper time_ids for SDXL (original_size, crop_coords, target_size)
        add_time_ids = torch.tensor(
            [[resolution, resolution, 0, 0, resolution, resolution]],
            dtype=torch.float32, device="cuda",
        )

        # Sample noise and timesteps
        noise = torch.randn_like(latents)
        timesteps = torch.randint(
            0, noise_scheduler.config.num_train_timesteps,
            (latents.shape[0],), device="cuda"
        ).long()
        noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

        # Predict noise
        added_cond_kwargs = {
            "text_embeds": pooled_prompt_embeds,
            "time_ids": add_time_ids,
        }
        noise_pred = pipe.unet(
            noisy_latents, timesteps, prompt_embeds,
            added_cond_kwargs=added_cond_kwargs,
        ).sample

        # MSE loss in fp32
        loss = torch.nn.functional.mse_loss(noise_pred, noise)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
        optimizer.step()
        optimizer.zero_grad()

        total_loss += loss.item()
        num_steps += 1

        if step % 50 == 0:
            logger.info(f"  Epoch {epoch+1}, step {step}/{len(dataloader)}, loss: {loss.item():.6f}")

    avg_loss = total_loss / max(num_steps, 1)
    logger.info(f"Epoch {epoch+1}/{num_epochs}, avg loss: {avg_loss:.6f}")

    # Save every 5 epochs
    if (epoch + 1) % 5 == 0:
        save_path = f"models/style_learner/teded_style_v1_epoch{epoch+1}"
        pipe.unet.save_pretrained(save_path)
        logger.info(f"Checkpoint saved: {save_path}")

# Save final
final_path = "models/style_learner/teded_style_v1"
pipe.unet.save_pretrained(final_path)
logger.info(f"Final LoRA saved: {final_path}")
print("LoRA training complete!")
TRAINEOF

echo "=== ALL COMPLETE: $(date) ==="
ls -lh models/style_learner/
