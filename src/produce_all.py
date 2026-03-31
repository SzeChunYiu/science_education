"""
produce_all.py — Mass production runner for all 189 physics episode scripts.

Uses a multiprocessing pool to render episodes in parallel.

Run:
    python3 src/produce_all.py [--workers N] [--fps 30] [--crf 28] [--resume]

Outputs to: output/physics/.../media/ep*.mp4
"""
import sys, os, time, json, argparse, multiprocessing as mp, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline.episode_renderer import render_episode


def _qc_mp4(output_mp4: str) -> dict:
    """Run post-render QC checks on a rendered MP4 via ffprobe."""
    issues = []
    duration_video = 0.0
    has_audio = False
    resolution = "0x0"

    # Check file exists and is large enough
    if not os.path.exists(output_mp4):
        issues.append("file does not exist")
        return {"qc_status": "fail", "qc_issues": issues,
                "duration_video": duration_video, "has_audio": has_audio,
                "resolution": resolution}

    size_bytes = os.path.getsize(output_mp4)
    if size_bytes < 50 * 1024:
        issues.append(f"file too small: {size_bytes} bytes (< 50KB)")

    # Run ffprobe to inspect streams
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", output_mp4],
            capture_output=True, text=True, timeout=30
        )
        probe = json.loads(proc.stdout) if proc.stdout else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        issues.append(f"ffprobe failed: {e}")
        return {"qc_status": "fail", "qc_issues": issues,
                "duration_video": duration_video, "has_audio": has_audio,
                "resolution": resolution}

    streams = probe.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    if not video_streams:
        issues.append("no video stream found")
    else:
        vs = video_streams[0]
        width = vs.get("width", 0)
        height = vs.get("height", 0)
        resolution = f"{width}x{height}"
        if width <= 0 or height <= 0:
            issues.append(f"invalid resolution: {resolution}")
        # Parse duration from video stream
        raw_dur = vs.get("duration") or vs.get("tags", {}).get("DURATION")
        if raw_dur:
            try:
                duration_video = float(raw_dur)
            except (ValueError, TypeError):
                pass
        if duration_video <= 5.0:
            issues.append(f"video duration too short: {duration_video:.2f}s (<= 5.0s)")

    if not audio_streams:
        issues.append("no audio stream found")
    else:
        has_audio = True

    qc_status = "fail" if issues else "pass"
    return {"qc_status": qc_status, "qc_issues": issues,
            "duration_video": duration_video, "has_audio": has_audio,
            "resolution": resolution}


def render_one(args):
    script_path, output_mp4, fps, crf = args
    try:
        t0 = time.time()
        render_episode(script_path, output_mp4, fps=fps, crf=crf, verbose=False)
        elapsed = time.time() - t0
        size_mb = os.path.getsize(output_mp4) / 1024 / 1024
        result = {"status": "ok", "script": script_path, "output": output_mp4,
                  "elapsed": elapsed, "size_mb": size_mb}
        qc = _qc_mp4(output_mp4)
        result.update(qc)
        if qc["qc_status"] == "fail":
            result["status"] = "qc_fail"
        return result
    except Exception as e:
        return {"status": "error", "script": script_path, "output": output_mp4,
                "elapsed": 0, "error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--fps",     type=int, default=30)
    ap.add_argument("--crf",     type=int, default=28)
    ap.add_argument("--resume",  action="store_true", help="Skip already-rendered episodes")
    args = ap.parse_args()

    physics_dir = ROOT / "output" / "physics"
    scripts = sorted(physics_dir.rglob("*_youtube_long.md"))
    print(f"Found {len(scripts)} scripts — workers={args.workers} fps={args.fps} crf={args.crf}")

    tasks = []
    for script in scripts:
        rel = script.relative_to(physics_dir)
        out_mp4 = script.parent.parent / "media" / (script.stem + ".mp4")
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and out_mp4.exists():
            continue
        tasks.append((str(script), str(out_mp4), args.fps, args.crf))

    print(f"Tasks to render: {len(tasks)} (skipped {len(scripts)-len(tasks)} existing)")
    if not tasks:
        print("Nothing to do.")
        return

    results = []
    t_start = time.time()
    with mp.Pool(processes=args.workers) as pool:
        for i, result in enumerate(pool.imap_unordered(render_one, tasks), 1):
            status = result["status"]
            name = Path(result["script"]).name
            if status == "ok":
                print(f"[{i}/{len(tasks)}] OK  {name}  {result['elapsed']:.0f}s  {result['size_mb']:.1f}MB")
            else:
                print(f"[{i}/{len(tasks)}] ERR {name}  {result.get('error','')[:80]}")
            results.append(result)

    elapsed_total = time.time() - t_start
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    qc_fail = sum(1 for r in results if r["status"] == "qc_fail")

    log_path = ROOT / "output" / "production_log.json"
    with open(log_path, "w") as f:
        json.dump({"started": t_start, "elapsed": elapsed_total, "results": results}, f, indent=2)

    print(f"\nDone: {ok} rendered, {err} errors, QC failures: {qc_fail} in {elapsed_total/60:.1f} min")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
