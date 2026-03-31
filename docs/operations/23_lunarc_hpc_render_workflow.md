# LUNARC HPC Render Workflow

## Overview

All 189 episode MP4s are rendered on the LUNARC HPC cluster (cosmos.lunarc.lu.se) using a SLURM array job. This is ~10× faster than local production:

- **Local (M3 Max, 4 workers):** ~5.3 hours total
- **LUNARC (189 parallel jobs, lu48 partition):** ~31 minutes total

Each episode renders independently in its own SLURM task, so 189 jobs run simultaneously across the cluster.

---

## Infrastructure

### SSH Access

```bash
# Check if connection is active
ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh

# Verify connection
ssh lunarc "hostname && whoami"
```

SSH config alias `lunarc` points to `cosmos.lunarc.lu.se` with a persistent ControlMaster socket (7-day TTL). The `lunarc-init.sh` script handles password + TOTP authentication automatically.

### Remote Paths

| Path | Description |
|------|-------------|
| `/projects/hep/fs10/shared/nnbar/billy/science_education/` | Project root |
| `.../science_education/src/` | Python source code |
| `.../science_education/output/physics/` | Episode scripts (markdown) |
| `.../science_education/episode_list.txt` | Sorted list of 189 `*_youtube_long.md` paths |
| `.../science_education/render_episodes.slurm` | SLURM array job script |
| `.../science_education/logs/` | Per-job stdout/stderr logs |
| `.../science_education/tmp/` | Temporary frame/scene directories during rendering |
| `/projects/hep/fs10/shared/nnbar/billy/packages/science_edu/` | Conda environment |
| `/projects/hep/fs10/shared/nnbar/billy/conda_pkgs/` | Conda package cache |

### Conda Environment

Location: `/projects/hep/fs10/shared/nnbar/billy/packages/science_edu/`

Contains:
- Python 3.11.15
- Pillow (PIL image compositing)
- FFmpeg 8.0.1 (frame stitching + MP4 encoding)
- Manim CE (equation animation — installed separately)

Created with:
```bash
module load Anaconda3/2024.06-1
CONDARC=/projects/hep/fs10/shared/nnbar/billy/science_education/condarc_tmp.yaml \
  conda create -p /projects/hep/fs10/shared/nnbar/billy/packages/science_edu \
  python=3.11 pillow ffmpeg -c conda-forge -y
```

The `condarc_tmp.yaml` sets `pkgs_dirs` to the project space (home quota was insufficient).

---

## Standard Workflow

### Step 1 — Sync code and scripts to LUNARC

Run from local machine after any code changes:

```bash
# Sync source code
rsync -avz \
  --exclude='__pycache__' --exclude='*.pyc' \
  /Users/billy/Desktop/projects/science_education/src/ \
  lunarc:/projects/hep/fs10/shared/nnbar/billy/science_education/src/

# Sync episode scripts (scripts only, no MP4s)
rsync -avz \
  --exclude='*.mp4' --exclude='*.png' --exclude='media/' \
  /Users/billy/Desktop/projects/science_education/output/physics/ \
  lunarc:/projects/hep/fs10/shared/nnbar/billy/science_education/output/physics/
```

### Step 2 — Regenerate episode list (if new episodes added)

```bash
ssh lunarc "find /projects/hep/fs10/shared/nnbar/billy/science_education/output/physics \
  -name '*youtube_long.md' | sort \
  > /projects/hep/fs10/shared/nnbar/billy/science_education/episode_list.txt && \
  wc -l /projects/hep/fs10/shared/nnbar/billy/science_education/episode_list.txt"
```

Update the `--array=1-N` line in `render_episodes.slurm` to match the count.

### Step 3 — Submit SLURM array job

```bash
ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/science_education && sbatch render_episodes.slurm"
```

For a single test episode first:
```bash
ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/science_education && sbatch --array=1-1 render_episodes.slurm"
```

### Step 4 — Monitor progress

```bash
# Overall status
ssh lunarc "squeue -u scyiu -o '%.10i %.18j %.8T %.10M %.12l %.20R'"

# Count completed episodes
ssh lunarc "find /projects/hep/fs10/shared/nnbar/billy/science_education/output/physics \
  -name '*_youtube_long.mp4' | wc -l"

# Check a specific job log
ssh lunarc "cat /projects/hep/fs10/shared/nnbar/billy/science_education/logs/render_1_JOBID.out"
ssh lunarc "cat /projects/hep/fs10/shared/nnbar/billy/science_education/logs/render_1_JOBID.err"
```

### Step 5 — Sync results back to local

```bash
rsync -avz \
  lunarc:/projects/hep/fs10/shared/nnbar/billy/science_education/output/physics/ \
  /Users/billy/Desktop/projects/science_education/output/physics/ \
  --include='*.mp4' --include='*/' --exclude='*'
```

---

## SLURM Job Details

**Script:** `render_episodes.slurm`

| Parameter | Value |
|-----------|-------|
| Partition | lu48 |
| Account | lu2025-2-51 |
| Array | 1-189 (one task per episode) |
| CPUs per task | 4 |
| Memory per task | 8 GB |
| Time limit | 1 hour |

Each task:
1. Reads line N from `episode_list.txt` to get the script path
2. Derives the output MP4 path: `<ep_dir>/media/<script_stem>.mp4`
3. Skips if MP4 already exists (idempotent — safe to re-run)
4. Calls `render_episode()` from `src/pipeline/episode_renderer.py`
5. Logs SUCCESS/FAILED + output path to stdout

---

## Re-rendering After Code Changes

The SLURM job is idempotent — already-rendered episodes are skipped. To force re-render specific episodes, delete their MP4 files first:

```bash
# Delete specific episode
ssh lunarc "rm /projects/.../ep01_why_things_stop/media/ep01_youtube_long.mp4"

# Delete all (start from scratch)
ssh lunarc "find /projects/hep/fs10/shared/nnbar/billy/science_education/output/physics \
  -name '*_youtube_long.mp4' -delete"
```

---

## Manim CE Integration (Planned)

Manim Community Edition is installed (or being installed) in the science_edu conda env to enable LaTeX-quality equation animations. See `docs/operations/24_manim_equation_animations.md` for integration details.

Key benefit: `TransformMatchingTex` enables smooth morphing between equation forms (e.g., `p = mv` → `F = dp/dt`) with per-term color highlights — far superior to PIL text rendering for educational math content.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ffmpeg not found on PATH` | Conda bin not in PATH | Ensure `export PATH=$ENV_BIN:$PATH` is in SLURM script |
| `NoWritablePkgsDirError` | Home quota issue | Use `CONDARC=condarc_tmp.yaml` pointing to project space |
| Job stays PENDING | lu48 queue busy | Normal — wait; all nodes in `mixed` state have free slots |
| Python import errors | PYTHONPATH not set | Ensure `PYTHONPATH=$BASE` is set before python call |
| Empty output files | Process hung (infinite loop) | Check `render_1_JOBID.err` for traceback |
