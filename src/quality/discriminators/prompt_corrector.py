"""Diagnose semantic rejections and rewrite SD prompts.

Uses BLIP captioning + NLI to identify mismatches between generated
images and narration, then rewrites the prompt to fix the mismatch.

Falls back gracefully if models are not available -- returns the
original prompt unchanged.
"""
import logging
from pathlib import Path
from typing import Union

from PIL import Image

logger = logging.getLogger(__name__)


class PromptCorrector:
    """Diagnose image-narration mismatches and correct SD prompts.

    Pipeline:
        1. Generate BLIP caption of the image (~1GB model)
        2. Run NLI between caption and narration (cross-encoder, ~400MB)
        3. If contradiction found: identify mismatching elements
        4. Rewrite prompt: remove incorrect element, add correct with weight boost

    Args:
        device: Torch device string (default "cpu" -- these models are small).
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._captioner = None
        self._captioner_processor = None
        self._nli_model = None
        self._nli_tokenizer = None
        self._loaded = False

    def _load_models(self):
        """Lazy-load captioning and NLI models."""
        if self._loaded:
            return

        # Load BLIP captioner
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration

            model_name = "Salesforce/blip-image-captioning-base"
            self._captioner_processor = BlipProcessor.from_pretrained(model_name)
            self._captioner = BlipForConditionalGeneration.from_pretrained(
                model_name
            )
            self._captioner.to(self.device)
            self._captioner.eval()
            logger.info(f"Loaded BLIP captioner ({model_name})")
        except ImportError:
            logger.warning(
                "transformers not available for BLIP captioning. "
                "Prompt correction will be disabled."
            )
        except Exception as e:
            logger.warning(f"Failed to load BLIP captioner: {e}")

        # Load NLI cross-encoder
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            nli_name = "cross-encoder/nli-deberta-v3-small"
            self._nli_tokenizer = AutoTokenizer.from_pretrained(nli_name)
            self._nli_model = AutoModelForSequenceClassification.from_pretrained(
                nli_name
            )
            self._nli_model.to(self.device)
            self._nli_model.eval()
            logger.info(f"Loaded NLI model ({nli_name})")
        except ImportError:
            logger.warning(
                "transformers not available for NLI. "
                "Prompt correction will be disabled."
            )
        except Exception as e:
            logger.warning(f"Failed to load NLI model: {e}")

        self._loaded = True

    def diagnose_and_correct(
        self,
        image: Union[Image.Image, Path, str],
        narration: str,
        original_prompt: str,
    ) -> tuple[str, str]:
        """Diagnose semantic mismatch and correct the prompt.

        Args:
            image: Generated image (PIL Image or path).
            narration: Narration text the image should match.
            original_prompt: The SD prompt that produced the image.

        Returns:
            Tuple of (corrected_prompt, diagnosis_log).
            If no correction needed or models unavailable, returns
            (original_prompt, diagnosis_log).
        """
        self._load_models()

        # Load image if path
        if isinstance(image, (str, Path)):
            try:
                image = Image.open(image).convert("RGB")
            except Exception as e:
                log = f"Failed to load image: {e}"
                logger.warning(log)
                return original_prompt, log

        # Step 1: Generate caption
        caption = self._caption_image(image)
        if not caption:
            log = "Captioning unavailable, returning original prompt"
            logger.info(log)
            return original_prompt, log

        # Step 2: Check NLI between caption and narration
        nli_result = self._check_nli(caption, narration)
        log_parts = [
            f"Caption: {caption}",
            f"Narration: {narration[:200]}",
            f"NLI result: {nli_result}",
        ]

        if nli_result["label"] != "contradiction":
            log = " | ".join(log_parts + ["No contradiction detected"])
            logger.info(log)
            return original_prompt, log

        # Step 3: Identify mismatch and rewrite prompt
        corrected, correction_detail = self._rewrite_prompt(
            original_prompt, caption, narration
        )
        log_parts.append(f"Correction: {correction_detail}")
        log = " | ".join(log_parts)
        logger.info(f"Prompt corrected: {correction_detail}")

        return corrected, log

    def _caption_image(self, image: Image.Image) -> str:
        """Generate a text caption for the image using BLIP."""
        if self._captioner is None or self._captioner_processor is None:
            return ""

        try:
            import torch

            inputs = self._captioner_processor(
                image, return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                out = self._captioner.generate(**inputs, max_new_tokens=50)

            caption = self._captioner_processor.decode(
                out[0], skip_special_tokens=True
            )
            return caption.strip()
        except Exception as e:
            logger.warning(f"Caption generation failed: {e}")
            return ""

    def _check_nli(self, caption: str, narration: str) -> dict:
        """Run NLI between image caption and narration text.

        Returns:
            Dict with "label" (entailment/neutral/contradiction)
            and "scores" dict.
        """
        if self._nli_model is None or self._nli_tokenizer is None:
            return {"label": "neutral", "scores": {}}

        try:
            import torch

            # Truncate narration to keep within model limits
            narration_short = narration[:256]

            inputs = self._nli_tokenizer(
                caption, narration_short,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            ).to(self.device)

            with torch.no_grad():
                logits = self._nli_model(**inputs).logits

            probs = torch.softmax(logits, dim=-1)[0]

            # Label mapping: 0=contradiction, 1=entailment, 2=neutral
            labels = ["contradiction", "entailment", "neutral"]
            scores = {
                label: round(probs[i].item(), 3) for i, label in enumerate(labels)
            }
            predicted = labels[probs.argmax().item()]

            return {"label": predicted, "scores": scores}
        except Exception as e:
            logger.warning(f"NLI check failed: {e}")
            return {"label": "neutral", "scores": {}}

    def _rewrite_prompt(
        self,
        original_prompt: str,
        caption: str,
        narration: str,
    ) -> tuple[str, str]:
        """Rewrite the prompt to fix identified mismatch.

        Strategy:
            - Extract key nouns from caption (what the image shows)
            - Extract key nouns from narration (what it should show)
            - Remove caption-only elements from prompt
            - Add narration elements with weight boost

        Returns:
            (corrected_prompt, explanation)
        """
        caption_words = set(self._extract_content_words(caption))
        narration_words = set(self._extract_content_words(narration))

        # Words in caption but not narration = potentially wrong elements
        wrong_elements = caption_words - narration_words
        # Words in narration but not caption = missing elements
        missing_elements = narration_words - caption_words

        corrected = original_prompt

        # Remove wrong elements from prompt (if they appear)
        for word in wrong_elements:
            if word.lower() in corrected.lower():
                # Simple removal -- replace word with empty string
                import re
                corrected = re.sub(
                    rf"\b{re.escape(word)}\b", "", corrected, flags=re.IGNORECASE
                )

        # Clean up doubled spaces/commas from removals
        import re
        corrected = re.sub(r"\s+", " ", corrected)
        corrected = re.sub(r",\s*,", ",", corrected)
        corrected = corrected.strip(" ,")

        # Add missing elements with emphasis
        if missing_elements:
            missing_str = ", ".join(sorted(missing_elements)[:5])
            corrected = f"{corrected}, ({missing_str}:1.3)"

        explanation = (
            f"Removed: {sorted(wrong_elements)[:5]}, "
            f"Added: {sorted(missing_elements)[:5]}"
        )

        return corrected, explanation

    def _extract_content_words(self, text: str) -> list[str]:
        """Extract meaningful content words (nouns, adjectives) from text."""
        import re

        # Simple approach: remove stop words, keep words > 3 chars
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "this", "that", "these", "those", "with", "from", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "over", "then", "than", "some", "such",
            "only", "very", "just", "about", "also", "more", "most",
            "other", "each", "every", "both", "few", "all", "any",
            "and", "but", "or", "nor", "not", "for", "yet", "so",
        }

        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        return [w for w in words if w not in stop_words]

    def unload(self):
        """Free model memory."""
        self._captioner = None
        self._captioner_processor = None
        self._nli_model = None
        self._nli_tokenizer = None
        self._loaded = False

        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except ImportError:
            pass

        logger.info("Prompt corrector models unloaded")
