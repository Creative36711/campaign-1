#!/usr/bin/env python3
"""Finish generated sprite sources and the selected Registrar's voice.

Raw AI output is rebuildable and ignored. Deliverable PNGs/MP3s are committed.
Usage: .venv/bin/python tools/media_finish.py --sprites --registrar
No generated music/SFX: the audio effect below is applied only to speech.
"""
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image
from scipy import ndimage, signal
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "_ai-temp/raw"
SPRITES = ["vex", "dozh", "zhuk", "kell", "resh", "ayla", "registrar", "vein", "dead_guard"]


def chroma_to_alpha(source: Path, dest: Path) -> dict:
    """Key green dominance, preserve blue mineral seams, dematte edge pixels.

    Both fully transparent backgrounds and non-exact green mattes are accepted.
    Isolated matte speckles are dropped, holes (hook, fingers) stay transparent.
    No rectangular crop of the source portrait is used as a sprite.
    """
    rgba = np.array(Image.open(source).convert("RGBA"), dtype=np.float32) / 255.0
    rgb = rgba[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    excess = g - np.maximum(r, b)
    alpha = rgba[..., 3].copy()
    key_alpha = np.clip((0.18 - excess) / 0.12, 0.0, 1.0)
    alpha *= np.where(g > 0.25, key_alpha, 1.0)

    components, count = ndimage.label(alpha > 0.12)
    if count == 0:
        raise ValueError(f"No foreground: {source}")
    sizes = np.bincount(components.ravel())
    largest = int(sizes[1:].argmax()) + 1
    keep_ids = np.flatnonzero(sizes >= max(16, sizes[largest] * 0.00003))
    keep_ids = keep_ids[keep_ids != 0]
    mask = np.isin(components, keep_ids)
    # Keep antialiasing around retained shapes, not loose background speckles.
    near_mask = ndimage.binary_dilation(mask, iterations=2)
    alpha[~near_mask] = 0.0
    edge = (alpha > 0.0) & (alpha < 0.995)
    # Remove green matte contamination; untouched solid pixels retain colour.
    rgb[..., 1] = np.where(edge, np.minimum(g, np.maximum(r, b)), g)
    rgb[alpha <= 0.0] = 0.0

    out = Image.fromarray(np.clip(np.dstack([rgb, alpha]) * 255.0, 0, 255).astype(np.uint8))
    bbox = out.getchannel("A").getbbox()
    if not bbox:
        raise ValueError(f"Empty keyed sprite: {source}")
    out = out.crop(bbox)
    # Bound final media size; transparent padding ~2% keeps all fingers/boots.
    max_size = (1200, 560) if "dead_guard" in dest.name else (740, 1100)
    out.thumbnail(max_size, Image.Resampling.LANCZOS)
    pad = max(8, round(max(out.size) * 0.018))
    framed = Image.new("RGBA", (out.width + pad * 2, out.height + pad * 2), (0, 0, 0, 0))
    framed.paste(out, (pad, pad))
    dest.parent.mkdir(parents=True, exist_ok=True)
    framed.save(dest, optimize=True)
    a = np.asarray(framed.getchannel("A"))
    assert all(a[y, x] == 0 for y, x in [(0, 0), (0, -1), (-1, 0), (-1, -1)])
    return {"path": str(dest.relative_to(ROOT)), "size": list(framed.size),
            "alpha_bbox": list(framed.getchannel("A").getbbox()),
            "transparent_fraction": round(float(np.mean(a == 0)), 4)}


def audio_metrics(path: Path) -> dict:
    x, sr = sf.read(path, dtype="float64", always_2d=True)
    rms = float(np.sqrt(np.mean(x * x)))
    peak = float(np.max(np.abs(x)))
    return {"path": str(path.relative_to(ROOT)), "duration_s": round(len(x) / sr, 3),
            "sample_rate": sr, "channels": x.shape[1],
            "rms_db": round(20 * math.log10(max(rms, 1e-12)), 2),
            "peak_db": round(20 * math.log10(max(peak, 1e-12)), 2)}


def robotic_voice(source: Path, dest: Path) -> dict:
    x, sr = sf.read(source, dtype="float64", always_2d=True)
    x = x.mean(axis=1)
    # A restrained speaking-grille colour; 82% intelligible dry speech remains.
    sos = signal.butter(3, [145, min(6000, sr * 0.44)], btype="bandpass", fs=sr, output="sos")
    x = signal.sosfilt(sos, x)
    t = np.arange(len(x)) / sr
    mechanical = x * np.sin(2 * np.pi * 68.0 * t)
    y = x * 0.82 + mechanical * 0.18
    # Short comb resonances, no tail/echo between separate sentences.
    for seconds, gain in [(0.011, 0.12), (0.017, -0.08)]:
        delay = round(sr * seconds)
        if delay < len(x):
            y[delay:] += gain * x[:-delay]
    rms = float(np.sqrt(np.mean(y * y)))
    if rms <= 1e-7:
        raise ValueError(f"Silent voice source: {source}")
    y *= 10 ** (-19 / 20) / rms
    # Soft peak guard prevents hard clipping. Recalculate gain after limiting.
    ceiling = 10 ** (-2.5 / 20)
    for _ in range(3):
        y = ceiling * np.tanh(y / ceiling)
        gain = 10 ** (-19 / 20) / float(np.sqrt(np.mean(y * y)))
        y *= gain
    y *= min(1.0, ceiling / float(np.max(np.abs(y))))
    wav = io.BytesIO()
    sf.write(wav, y, sr, format="WAV", subtype="PCM_24")
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                    "-y", "-i", "pipe:0", "-ac", "1", "-ar", "48000",
                    "-codec:a", "libmp3lame", "-b:a", "128k", str(dest)],
                   input=wav.getvalue(), check=True)
    metrics = audio_metrics(dest)
    if metrics["peak_db"] > -1.8 or not -22 <= metrics["rms_db"] <= -17:
        raise ValueError(f"Registrar loudness outside guardrails: {metrics}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprites", action="store_true")
    parser.add_argument("--registrar", action="store_true")
    args = parser.parse_args()
    report = {}
    if args.sprites:
        report["sprites"] = [chroma_to_alpha(RAW / f"sprite_{name}.png",
                              ROOT / f"assets/img/{'items' if name == 'dead_guard' else 'npc'}/sprite_{name}.png")
                             for name in SPRITES]
        with Image.open(RAW / "item_dead_guard.jpg") as image:
            image.convert("RGB").save(ROOT / "assets/img/items/item_dead_guard.jpg", quality=94)
    if args.registrar:
        report["registrar"] = [robotic_voice(RAW / f"registrar_{i}.mp3",
                                 ROOT / f"assets/voice/registrar_{i}.mp3") for i in range(1, 11)]
    out = ROOT / "tools/media_finish_report.json"
    old = json.loads(out.read_text()) if out.exists() else {}
    old.update(report)
    out.write_text(json.dumps(old, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
