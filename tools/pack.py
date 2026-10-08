#!/usr/bin/env python3
"""Validate and atomically build one complete, reproducible Chronicle package.

Only root documents, declared canonical modules, Ink + editor sidecars and all
local assets are included. Task instructions, tests and tools never ship.
Run: .venv/bin/python tools/pack.py
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'campaign-1.chronicle'
MODULES = ['scenes','entities','rules','arenas','quests','cutscenes','recipes','codex','encounters']
ALREADY_COMPRESSED = {'.jpg','.jpeg','.png','.webp','.mp3','.ogg','.woff2','.woff'}


def collect_files(root: Path = ROOT) -> list[str]:
    manifest = json.loads((root / 'manifest.json').read_text())
    files = {'campaign.json','world.json','manifest.json'}
    for section in MODULES:
        for name in manifest.get(section, []):
            if Path(name).name != name or '\\' in name:
                raise ValueError(f'Manifest requires basenames: {section}/{name}')
            files.add(section + '/' + name)
    for name in manifest.get('dialogues', []):
        if Path(name).name != name or '\\' in name:
            raise ValueError('Dialogue basename expected: ' + name)
        stem = name.removesuffix('.ink')
        files.update(['dialogues/' + stem + '.ink', 'dialogues/' + stem + '.dlg.json'])
    files.update(p.relative_to(root).as_posix() for p in (root / 'assets').rglob('*') if p.is_file())
    for rel in files:
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('External/symlink resource is not packageable: ' + rel)
    return sorted(files)


def build(root: Path = ROOT, out: Path = OUT):
    files = collect_files(root)
    # Never truncate the last valid deliverable on a failed build.
    scratch = root / '_ai-temp' / 'incoming'
    scratch.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='package-', suffix='.tmp', dir=scratch)
    os.close(fd)
    tmp = Path(name)
    try:
        with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for rel in files:
                info = zipfile.ZipInfo(rel, date_time=(1980,1,1,0,0,0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_STORED if Path(rel).suffix.lower() in ALREADY_COMPRESSED else zipfile.ZIP_DEFLATED
                z.writestr(info, (root / rel).read_bytes(), compresslevel=9)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None:
                raise ValueError('ZIP CRC check failed')
            if z.namelist() != files or len(z.namelist()) != len(set(z.namelist())):
                raise ValueError('Archive file list mismatch')
            for rel in files:
                if z.read(rel) != (root / rel).read_bytes():
                    raise ValueError('Changed/mismatched source during build: ' + rel)
        os.replace(tmp, out)
    finally:
        tmp.unlink(missing_ok=True)
    report = {'file':out.name, 'campaign_id':json.loads((root/'campaign.json').read_text())['id'],
              'file_count':len(files), 'asset_count':sum(p.startswith('assets/') for p in files),
              'bytes':out.stat().st_size, 'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
              'crc_ok':True, 'all_entries_match_sources':True,
              'excluded':['__chronicle_ai__','tools','tests','PROJECT_PLAN.md','README.md'],
              'files':files}
    return report


def main():
    subprocess.run([sys.executable,str(ROOT/'tools/validate.py')],cwd=ROOT,check=True)
    report = build()
    (ROOT/'tools/package-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f"Архив: {report['file']} — {report['file_count']} файлов, {report['bytes']/1048576:.2f} МиБ; CRC и все байты совпадают с исходниками.")
    print('SHA256:',report['sha256'])
    return 0

if __name__ == '__main__': raise SystemExit(main())
