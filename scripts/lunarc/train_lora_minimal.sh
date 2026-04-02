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
mkdir -p logs models/style_learner

echo "=== Started: $(date) ==="
nvidia-smi | head -3

python3 << 'TRAINEOF'
import torch
import logging
from pathlib import Path
from diffusers import AutoencoderKL, UNet2DConditionModel, DDPMScheduler
from transformers import CLIPTextModel, CLIPTextModelWithProjection, CLIPTokenizer
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

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        caption_path = img_path.with_suffix(".txt")
        image = Image.open(img_path).convert("RGB")
        caption = caption_path.read_text().strip() if caption_path.exists() else "teded_style educational illustration"
        return {"image": self.transform(image), "caption": caption}


model_id = "stabilityai/stable-diffusion-xl-base-1.0"
resolution = 1024

# Load components separately
logger.info("Loading SDXL components...")
vae = AutoencoderKL.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float32).to("cuda")
unet = UNet2DConditionModel.from_pretrained(model_id, subfolder="unet", torch_dtype=torch.float32).to("cuda")
text_encoder = CLIPTextModel.from_pretrained(model_id, subfolder="text_encoder", torch_dtype=torch.float32).to("cuda")
text_encoder_2 = CLIPTextModelWithProjection.from_pretrained(model_id, subfolder="text_encoder_2", torch_dtype=torch.float32).to("cuda")
tokenizer = CLIPTokenizer.from_pretrained(model_id, subfolder="tokenizer")
tokenizer_2 = CLIPTokenizer.from_pretrained(model_id, subfolder="tokenizer_2")
noise_scheduler = DDPMScheduler.from_pretrained(model_id, subfolder="scheduler")

vae.requires_grad_(False)
text_encoder.requires_grad_(False)
text_encoder_2.requires_grad_(False)

# Apply LoRA to UNet
lora_config = LoraConfig(
    r=32,
    lora_alpha=16,
    target_modules=["to_k", "to_q", "to_v", "to_out.0"],
    lora_dropout=0.05,
)
unet = get_peft_model(unet, lora_config)
unet.train()

trainable_params = [p for p in unet.parameters() if p.requires_grad]
logger.info(f"Trainable params: {sum(p.numel() for p in trainable_params):,}")

# Dataset
dataset = LoraImageDataset("data/lora_training/teded_style", resolution=resolution)
dataloader = DataLoader(dataset, batch_size=1, shuffle=True, num_workers=2)
logger.info(f"Dataset: {len(dataset)} images")

# Optimizer with lower LR
optimizer = torch.optim.AdamW(trainable_params, lr=5e-5, weight_decay=0.01)

def encode_text(prompt_list):
    """Encode text using both CLIP text encoders for SDXL."""
    # Tokenize for both encoders
    tokens_1 = tokenizer(prompt_list, padding="max_length", max_length=77, truncation=True, return_tensors="pt").input_ids.to("cuda")
    tokens_2 = tokenizer_2(prompt_list, padding="max_length", max_length=77, truncation=True, return_tensors="pt").input_ids.to("cuda")

    with torch.no_grad():
        enc_1 = text_encoder(tokens_1, output_hidden_states=True)
        enc_2 = text_encoder_2(tokens_2, output_hidden_states=True)

        # SDXL uses penultimate hidden states
        hidden_1 = enc_1.hidden_states[-2]
        hidden_2 = enc_2.hidden_states[-2]
        prompt_embeds = torch.cat([hidden_1, hidden_2], dim=-1)

        # Pooled output from text_encoder_2
        pooled = enc_2.text_embeds

    return prompt_embeds, pooled


num_epochs = 20
logger.info(f"Starting training for {num_epochs} epochs...")

for epoch in range(num_epochs):
    total_loss = 0.0
    for step, batch in enumerate(dataloader):
        images = batch["image"].to("cuda", dtype=torch.float32)
        captions = batch["caption"]

        # Encode images
        with torch.no_grad():
            latents = vae.encode(images).latent_dist.sample() * vae.config.scaling_factor

        # Encode text
        prompt_embeds, pooled_prompt_embeds = encode_text(list(captions))

        # Time IDs: [orig_h, orig_w, crop_top, crop_left, target_h, target_w]
        add_time_ids = torch.tensor(
            [[resolution, resolution, 0, 0, resolution, resolution]],
            dtype=torch.float32, device="cuda",
        )

        # Add noise
        noise = torch.randn_like(latents)
        timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device="cuda").long()
        noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

        # Predict
        added_cond_kwargs = {"text_embeds": pooled_prompt_embeds, "time_ids": add_time_ids}
        noise_pred = unet(noisy_latents, timesteps, prompt_embeds, added_cond_kwargs=added_cond_kwargs).sample

        loss = torch.nn.functional.mse_loss(noise_pred, noise)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
        optimizer.step()
        optimizer.zero_grad()

        total_loss += loss.item()
        if step % 50 == 0:
            logger.info(f"  Epoch {epoch+1}, step {step}/{len(dataloader)}, loss: {loss.item():.6f}")

    avg_loss = total_loss / len(dataloader)
    logger.info(f"Epoch {epoch+1}/{num_epochs}, avg loss: {avg_loss:.6f}")

    if (epoch + 1) % 5 == 0:
        save_path = f"models/style_learner/teded_style_v1_epoch{epoch+1}"
        unet.save_pretrained(save_path)
        logger.info(f"Saved: {save_path}")

unet.save_pretrained("models/style_learner/teded_style_v1")
logger.info("Final LoRA saved!")
print("LoRA training complete!")
TRAINEOF

echo "=== ALL COMPLETE: $(date) ==="
ls -lhR models/style_learner/ | head -20
