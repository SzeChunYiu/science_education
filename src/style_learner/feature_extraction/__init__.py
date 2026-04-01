"""Feature extraction pipeline for TED-Ed style learning.

Modules:
    clip_features       - CLIP embeddings and zero-shot scene classification
    camera_motion       - Optical flow camera motion classification
    text_layout         - OCR-based text region detection and tracking
    quality_scores      - Visual, audio, and composite quality scoring
    narration_alignment - Transcript-to-scene alignment with phase classification
    dataset_builder     - Unified dataset assembly and splitting
    extract_all         - Master orchestrator (CLI entry point)
"""
