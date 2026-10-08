#!/usr/bin/env python3
"""Validate all campaign module files against __chronicle_ai__/campaign.schema.json"""
import json, glob, sys
from jsonschema import Draft202012Validator

S = json.load(open('__chronicle_ai__/campaign.schema.json'))
D = S['$defs']
RESOLVER = S

def make_validator(defname):
    return Draft202012Validator({**S, '$ref': f'#/$defs/{defname}'}, resolver=None)

checks = [
    ('campaign.json', 'CampaignMeta'),
    ('world.json', 'WorldDef'),
    ('manifest.json', 'CampaignManifest'),
    ('encounters/encounters.json', 'EncounterFileDef'),
]
for f in sorted(glob.glob('scenes/*.json')): checks.append((f, 'SceneDef'))
for f in sorted(glob.glob('entities/*.json')): checks.append((f, 'EntityDef'))
for f in sorted(glob.glob('rules/rule_*.json')): checks.append((f, 'RuleDef'))
for f in sorted(glob.glob('quests/*.json')): checks.append((f, 'QuestDef'))
for f in sorted(glob.glob('arenas/*.json')): checks.append((f, 'ArenaDef'))
for f in sorted(glob.glob('cutscenes/*.json')): checks.append((f, 'CutsceneDef'))
for f in sorted(glob.glob('recipes/*.json')): checks.append((f, 'RecipeDef'))
for f in sorted(glob.glob('codex/*.json')): checks.append((f, 'CodexEntryDef'))
for f in sorted(glob.glob('dialogues/*.dlg.json')): checks.append((f, 'MonolithDialogue'))

errors = 0
for f, defname in checks:
    try:
        doc = json.load(open(f))
    except Exception as e:
        print(f"JSON PARSE FAIL {f}: {e}"); errors += 1; continue
    v = make_validator(defname)
    errs = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errs:
        errors += len(errs)
        print(f"== {f} ({defname}): {len(errs)} errors")
        for e in errs[:6]:
            print("   ", "/".join(map(str, e.absolute_path)) or "<root>", ":", e.message[:160])
print(f"\nTOTAL ERRORS: {errors} across {len(checks)} files")
sys.exit(1 if errors else 0)
