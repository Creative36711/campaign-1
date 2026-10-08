#!/usr/bin/env python3
"""Read-only audit of every registered sound, music track and voice file.

Writes tools/audio-audit.json and tools/audio-audit.md. It measures decoded
waveforms and checks all playback contexts; it does NOT claim to listen to audio.
Usage: .venv/bin/python tools/audit_audio.py
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
AMBIENT_IDS = {
    "snd_crowd", "snd_deep_drone", "snd_drops", "snd_fire", "snd_pump_amb",
    "snd_rain", "snd_water_amb", "snd_wind", "snd_city_amb", "snd_shaft_amb",
}


def metrics(path: Path) -> dict:
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if len(x) == 0:
        raise ValueError("empty audio")
    mono = x.mean(axis=1, dtype=np.float64)
    rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
    peak = float(np.max(np.abs(x)))
    win = max(1, round(sr * 0.1))
    n = len(mono) // win
    windows = mono[:n * win].reshape(n, win) if n else mono[None, :]
    quiet = np.sqrt(np.mean(windows ** 2, axis=1)) < 10 ** (-45 / 20)
    # An objective join proxy, not a claim that a loop sounds seamless.
    join = float(np.max(np.abs(x[0] - x[-1])))
    return {"duration_s": round(len(x) / sr, 3), "sample_rate": sr, "channels": x.shape[1],
            "rms_db": round(20 * math.log10(max(rms, 1e-12)), 2),
            "peak_db": round(20 * math.log10(max(peak, 1e-12)), 2),
            "silent_windows_fraction": round(float(np.mean(quiet)), 4),
            "near_clip_fraction": round(float(np.mean(np.abs(x) >= 0.999)), 7),
            "join_difference_db": round(20 * math.log10(max(join, 1e-12)), 2)}


def collect_usage(campaign: dict) -> dict:
    ids = {x["id"] for x in campaign["sounds"]}
    usage = defaultdict(list)
    files = [ROOT / "campaign.json", ROOT / "world.json"]
    for folder in ["scenes", "entities", "rules", "quests", "cutscenes", "dialogues", "recipes", "encounters"]:
        files += sorted((ROOT / folder).glob("*.json"))

    def walk(obj, file, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if file == "campaign.json" and key in {"sounds", "music_tracks", "design_doc"}:
                    continue
                if key == "id":
                    continue
                walk(value, file, f"{path}/{key}")
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, file, f"{path}/{i}")
        elif isinstance(obj, str) and obj in ids:
            mode = "ambient" if "/ambient/" in path else "stop" if "/stop_sound" in path else "one-shot"
            usage[obj].append({"file": file, "path": path, "mode": mode})
    for path in files:
        walk(json.loads(path.read_text()), str(path.relative_to(ROOT)))
    # Raw Ink is the runtime source; sidecar duplicates remain explicit in report.
    import re
    for path in sorted((ROOT / "dialogues").glob("*.ink")):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            for match in re.finditer(r'#\s*sfx:\s*(\w+)|play_sound\(\s*"(\w+)"', line):
                snd = match.group(1) or match.group(2)
                if snd in ids:
                    usage[snd].append({"file": str(path.relative_to(ROOT)), "path": f"line {i}", "mode": "one-shot"})
    return usage


def audit() -> dict:
    campaign = json.loads((ROOT / "campaign.json").read_text())
    usage = collect_usage(campaign)
    issues, sounds, music, voices = [], [], [], []
    cache = {}

    def read(src):
        if not isinstance(src, str) or not src.startswith("assets/"):
            issues.append(f"Источник не является локальной записью: {src}")
            return {}
        if src not in cache:
            try:
                cache[src] = metrics(ROOT / src)
            except Exception as exc:
                cache[src] = {"error": str(exc)}
                issues.append(f"Не декодируется {src}: {exc}")
        return cache[src]

    for sound in campaign["sounds"]:
        expected = sound["id"] in AMBIENT_IDS
        if sound.get("loop") is not expected:
            issues.append(f"Некорректный loop у {sound['id']}: {sound.get('loop')}, ожидается {expected}")
        sources = sound["src"] if isinstance(sound["src"], list) else [sound["src"]]
        rows = [{"path": src, **read(src)} for src in sources]
        contexts = usage[sound["id"]]
        if expected:
            one_shots = [u for u in contexts if u["mode"] == "one-shot"]
            if one_shots:
                issues.append(f"Фоновая петля {sound['id']} использована разово: " + "; ".join(f"{u['file']}{u['path']}" for u in one_shots))
        sounds.append({**sound, "sources": rows, "usage": contexts,
                       "decision": "Постоянный фоновый слой" if expected else "Разовый звук действия/сигнал/ответ"})
    for track in campaign["music_tracks"]:
        music.append({**track, "metrics": read(track["src"])})
        if track.get("loop") is not True:
            issues.append(f"У фонового музыкального трека {track['id']} отключён loop")
    for path in sorted((ROOT / "assets/voice").glob("*.mp3")):
        rel = str(path.relative_to(ROOT))
        row = {"path": rel, **read(rel)}
        if "error" not in row:
            if row["rms_db"] < -35 or row["silent_windows_fraction"] > 0.6 or row["duration_s"] < 0.5:
                issues.append(f"Подозрительная озвучка {rel}: RMS {row['rms_db']}, тишина {row['silent_windows_fraction']}")
            if row["near_clip_fraction"] > 0.005:
                issues.append(f"Клиппинг озвучки {rel}: {row['near_clip_fraction']}")
        voices.append(row)
    return {"method": "decoded waveform metrics and static playback-context audit, not listening or engine playtest",
            "sounds_count": len(sounds), "ambient_count": len(AMBIENT_IDS),
            "music_count": len(music), "voice_count": len(voices), "decoded_file_count": len(cache),
            "issues": issues, "sounds": sounds, "music": music, "voices": voices}


def write_report(report):
    (ROOT / "tools/audio-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Аудит звуков — 8 октября 2026", "",
             f"Проверено: {report['sounds_count']} звуков в реестре, {report['music_count']} музыкальных треков, {report['voice_count']} озвучек; декодировано {report['decoded_file_count']} отдельных файлов.",
             "", "Это измерения и проверка контекстов, не прослушивание и не плейтест движка.", "",
             "## Решения о повторении", "",
             "- Постоянные фоновые записи: 10 петель; короткие звуки — однократно.",
             "- «Гул Жилы» — короткий ответ персонажа, не бесконечная фоновая петля.",
             "- Для интро печки и жаровни отделён короткий `sfx_fire` (2,8 с из той же реальной CC0-записи), чтобы новый `loop` не создавал второй неуправляемый фон.",
             "- Музыка: существующие десять файлов CC0, все зациклены; новых синтетических звуков/музыки нет.", "",
             "| Звук | Подпись | Повтор | Длительность источников, с | Решение |", "| --- | --- | --- | --- | --- |"]
    for row in report["sounds"]:
        durations = ", ".join(str(x.get("duration_s", "ERROR")) for x in row["sources"])
        lines.append(f"| `{row['id']}` | {row['label']} | {'да' if row['loop'] else 'нет'} | {durations} | {row['decision']} |")
    lines += ["", "## Новый голос Регистратора", "", "Все десять реплик одного выбранного мастером голоса: умеренная металлическая окраска, без замены диктора. Точные параметры обработки — `tools/media_finish.py`.", "",
              "| Файл | Длительность, с | RMS, дБ | Пик, дБ |", "| --- | --- | --- | --- |"]
    for row in report["voices"]:
        if Path(row["path"]).name.startswith("registrar_"):
            lines.append(f"| `{Path(row['path']).name}` | {row.get('duration_s')} | {row.get('rms_db')} | {row.get('peak_db')} |")
    lines += ["", "## Требует внимания", ""]
    lines += [f"- {issue}" for issue in report["issues"]] or ["- Ошибок декодирования, неверных loop-контекстов, подозрительно тихих/пустых озвучек или существенного клиппинга по заданным порогам не найдено."]
    (ROOT / "tools/audio-audit.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    report = audit()
    write_report(report)
    print({key: report[key] for key in ["sounds_count", "ambient_count", "music_count", "voice_count", "decoded_file_count"]})
    for issue in report["issues"]:
        print("ATTENTION", issue)
    raise SystemExit(1 if report["issues"] else 0)
