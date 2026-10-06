#!/usr/bin/env python3
"""Звуковые крючки кампании: кто, где и чем звучит.

Движок умеет вешать звук на много мест разного масштаба — от реплики
до целой локации. Скрипт раскладывает звуки по всем этим местам разом,
чтобы таблица назначений лежала в одном файле и её можно было
перечитать, а не искать по сорока json.

Уровни, от крупного к мелкому:

1. `ui_sounds` — интерфейс: общий `panel_open` плюс отдельные звуки
   панелей (`panel:inventory` и т.п.) с каскадным откатом на общий.
2. `TravelConnection` — `depart_sound` (отправление), `sound` (путь),
   `arrive_sound` (прибытие): у каждого перехода между ярусами свой.
3. Музыка: `override_music` / `clear_music_override` — сюжетный оверрайд
   поверх музыки сцены (тревога, удушье, бой) и возврат к обычной.
4. Правила: `play_sound` — точный звук события (защёлка, гудок, плеск).
5. Рецепты: `sound` — чем звучит крафт (наковальня, котелок, ткань).
6. Реплики: `# sfx:` в ink и поле `sfx` в конструкторе.

Запуск: python3 tools/audio_hooks.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as fh:
        return json.load(fh)


def save(path, data):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f'записан {path}')


# ---------------------------------------------------------------- интерфейс
UI_SOUNDS = {
    # панели: свой звук у каждой, движок откатывается на общий panel_open
    'panel:inventory': 'snd_cloth',   # сумка дознавателя — брезент
    'panel:journal': 'snd_page',      # дело №137 — страница
    'panel:map': 'snd_paper',         # схема ярусов — разворот листа
    'panel:craft': 'sfx_anvil',       # верстак
    'panel:character': 'snd_cloth',
    'panel:codex': 'snd_paper',       # архив Надзора
    # предметы
    'equip': 'snd_latch',
    'unequip': 'snd_cloth',
    'item_get': 'sfx_pickup',
    'item_lose': 'snd_cloth',
    'craft': 'sfx_anvil',
    # бой
    'heal': 'sfx_lamp',
    'flee': 'sfx_step',
    'kill': 'sfx_crit',
}

NEW_SOUNDS = [
    {'id': 'sfx_hum', 'label': 'Гул жилы', 'src': 'assets/audio/sfx/sfx_hum.mp3'},
    {'id': 'sfx_rungs', 'label': 'Ступени лестницы', 'src': 'assets/audio/sfx/sfx_rungs.ogg'},
    {'id': 'sfx_wade', 'label': 'Шаг по воде', 'src': 'assets/audio/sfx/sfx_wade.ogg'},
]

# ------------------------------------------------------------------ дорога
# локация → локация: отправление, путь, прибытие
TRAVEL = {
    ('loc_surface', 'loc_gate'): ('snd_latch', 'sfx_step', 'sfx_door'),
    ('loc_gate', 'loc_surface'): ('sfx_door', 'sfx_step', 'snd_latch'),
    ('loc_surface', 'loc_pump7'): ('snd_latch', 'sfx_step', 'snd_creak'),
    ('loc_pump7', 'loc_surface'): ('snd_creak', 'sfx_step', 'snd_latch'),
    ('loc_gate', 'loc_pump7'): ('snd_chain', 'sfx_rungs', 'snd_creak'),
    ('loc_pump7', 'loc_gate'): ('snd_creak', 'sfx_rungs', 'snd_chain'),
    ('loc_pump7', 'loc_ward8'): ('snd_latch', 'sfx_wade', 'sfx_water'),
    ('loc_ward8', 'loc_pump7'): ('sfx_water', 'sfx_wade', 'snd_latch'),
    ('loc_ward8', 'loc_deep9'): ('snd_creak', 'sfx_step', 'snd_vent'),
    ('loc_deep9', 'loc_ward8'): ('snd_vent', 'sfx_step', 'snd_creak'),
}

# ------------------------------------------------------------------- крафт
RECIPES = {
    'recipe_bandage': 'snd_cloth',
    'recipe_bolt': 'sfx_anvil',
    'recipe_charge': 'snd_charge',
    'recipe_filter': 'sfx_gear',
    'recipe_repair_lamp': 'sfx_lamp',
    'recipe_tonic': 'snd_pot',
    'recipe_stew': 'snd_pot',
}

# ----------------------------------------------------------------- правила
# правило → список эффектов, которые надо дописать в конец
PS = lambda s, v=1.0: {'type': 'play_sound', 'sound': s, 'volume': v}
OM = lambda t, f=2: {'type': 'override_music', 'tracks': t, 'fade': f}

RULES = {
    'rule_air_warn': [PS('snd_vent', 0.7)],
    'rule_zero_air': [OM(['music_deep'], 2), PS('snd_vent', 1.0),
                      {'type': 'set_flag', 'flag': 'air_music'}],
    'rule_filter_bank1': [PS('snd_vent', 0.8)],
    'rule_filter_bank2': [PS('snd_vent', 0.8)],
    'rule_filter_spent': [PS('sfx_steam', 0.9)],
    'rule_ashfall': [PS('snd_vent', 0.6)],
    'rule_downpour': [PS('sfx_water', 1.0)],
    'rule_deadline_warn': [OM(['music_alarm'], 3), PS('sfx_horn', 0.9)],
    'rule_water_rises': [PS('sfx_wade', 0.9)],
    'rule_gate_first': [PS('sfx_door', 1.0)],
    'rule_sluice_first': [PS('sfx_water', 0.8)],
    'rule_install_valve': [PS('sfx_gear', 0.9)],
    'rule_open_cache': [PS('snd_stone', 0.9)],
    'rule_reveal_deep': [PS('snd_creak', 0.8)],
    'rule_watchman': [PS('sfx_gear', 0.7)],
    'rule_see_rot': [PS('sfx_water', 0.6)],
    'rule_hounds': [PS('snd_stone', 0.7)],
    'rule_camp_ambush': [PS('sfx_hit', 0.9)],
    'rule_kast_note': [PS('snd_paper', 0.7)],
    'rule_kell_token': [PS('snd_tag', 0.8)],
    'rule_zhuk_ledger': [PS('snd_page', 0.7)],
    'rule_roster_got': [PS('snd_paper', 0.7)],
    'rule_ira_story': [PS('snd_paper', 0.7)],
    'rule_ira_brother': [PS('snd_tag', 0.8)],
    'rule_zhuk_appears': [PS('sfx_coin', 0.8)],
    'rule_zhuk_info': [PS('sfx_coin', 0.8)],
    'rule_lockdown': [PS('snd_latch', 0.9)],
    'rule_end_silence': [PS('snd_charge', 1.0)],
    'rule_end_vein': [PS('sfx_hum', 1.0)],
    'rule_resh_found': [PS('sfx_hum', 0.6)],
}

# новое правило: снять оверрайд удушья, когда герой выбрался наверх
RULE_AIR_BACK = {
    'id': 'rule_air_restored',
    'label': 'Воздух снова есть',
    'once': False,
    'manual': False,
    'conditions': [
        {'type': 'flag_set', 'flag': 'air_music'},
        {'type': 'or', 'conditions': [
            {'type': 'player_enters_scene', 'scene': s}
            for s in ('scene_dry_row', 'scene_pump_hall', 'scene_gate_hall', 'scene_office')
        ]},
    ],
    'effects': [
        {'type': 'clear_music_override', 'fade': 3},
        {'type': 'clear_flag', 'flag': 'air_music'},
        {'type': 'show_message',
         'text': 'Воздух снова есть. Ты дышишь глубоко и слышишь, как город гудит дальше — без тебя, но и без воды.'},
    ],
    'chapter': 'ch_deep',
}

# --------------------------------------------------------------- предметы
ITEM_SOUNDS = {
    'item_filter': {'equip': 'snd_latch', 'unequip': 'snd_cloth', 'use': 'snd_vent'},
    'item_coat': {'equip': 'snd_cloth', 'unequip': 'snd_cloth'},
    'item_lamp': {'equip': 'sfx_lamp', 'unequip': 'snd_cloth'},
    'item_wrench': {'equip': 'snd_latch', 'unequip': 'snd_cloth'},
}

# ---------------------------------------------------------------- реплики
# файл → (начало реплики, звук)
LINES = [
    ('vex', 'Векс поднимает глаза от пульта', 'sfx_click'),
    ('vex', 'Он крутит маховик', 'sfx_gear'),
    ('registrar', 'Регистратор щёлкает реле', 'sfx_click'),
    ('registrar', 'Пломба предъявлена', 'snd_latch'),
    ('kell', 'Келл не встаёт', 'snd_blade'),
    ('kell', 'Келл смотрит на медь', 'snd_tag'),
    ('zhuk', 'Он протягивает руку', 'sfx_coin'),
    ('zhuk', 'Жук листает', 'snd_page'),
    ('ira', 'Она вытирает ладони', 'snd_cloth'),
    ('ira', 'Она берёт жетон', 'snd_tag'),
    ('resh', 'Он встаёт тяжело', 'snd_stone'),
    ('vein', 'Ты кладёшь ладонь на камень', 'sfx_hum'),
    ('vein', 'Молчание длится', 'sfx_hum'),
    ('kast', 'Она листает книгу', 'snd_page'),
    ('kast', 'Молчишь? Я запишу', 'snd_paper'),
    ('dozh', 'Дож вертит вещь', 'snd_latch'),
    ('ayla', 'Айла промокает бинт', 'sfx_water'),
]


def main():
    # 1. реестр звуков и интерфейс
    camp = load('campaign.json')
    ids = {s['id'] for s in camp['sounds']}
    for s in NEW_SOUNDS:
        if s['id'] not in ids:
            camp['sounds'].append(s)
            ids.add(s['id'])
    camp['sounds'].sort(key=lambda s: s['id'])
    ui = camp.setdefault('ui_sounds', {})
    ui.update({k: v for k, v in UI_SOUNDS.items() if k not in ui})
    save('campaign.json', camp)

    # 2. дорога
    world = load('world.json')
    done = 0
    for loc in world['regions'][0]['locations']:
        for conn in loc.get('travel_connections', []):
            key = (loc['id'], conn['to'])
            if key not in TRAVEL:
                print('нет звуков для перехода', key)
                continue
            dep, path, arr = TRAVEL[key]
            conn['depart_sound'] = dep
            conn['sound'] = path
            conn['arrive_sound'] = arr
            done += 1
    save('world.json', world)
    print('  переходов со звуком:', done)

    # 3. крафт
    for rid, snd in RECIPES.items():
        p = f'recipes/{rid}.json'
        try:
            r = load(p)
        except FileNotFoundError:
            print('нет рецепта', rid)
            continue
        r['sound'] = snd
        save(p, r)

    # 4. правила
    for rid, effects in RULES.items():
        p = f'rules/{rid}.json'
        try:
            r = load(p)
        except FileNotFoundError:
            print('нет правила', rid)
            continue
        have = {json.dumps(e, ensure_ascii=False, sort_keys=True) for e in r['effects']}
        for e in effects:
            key = json.dumps(e, ensure_ascii=False, sort_keys=True)
            if key in have:
                continue
            # звук вставляем перед финальными эффектами (финал, конец игры)
            tail = {'game_over_victory', 'game_over_death'}
            pos = len(r['effects'])
            for i, ex in enumerate(r['effects']):
                if ex.get('type') in tail:
                    pos = i
                    break
            r['effects'].insert(pos, e)
            have.add(key)
        save(p, r)

    # оверрайд боя у затвора: включить перед проверкой, снять после
    r = load('rules/rule_final_fight.json')
    r['effects'].insert(0, {'type': 'override_music', 'tracks': ['music_battle'], 'fade': 1.5})
    clear = {'type': 'clear_music_override', 'fade': 3}
    for e in r['effects']:
        if e.get('type') == 'skill_check_gate':
            e['success_effects'].append(dict(clear))
            fail = e.get('fail_effects') or []
            for f in fail:
                if f.get('type') == 'start_combat':
                    for key in ('on_victory', 'on_fled'):
                        f.setdefault(key, []).append(dict(clear))
    save('rules/rule_final_fight.json', r)

    # новое правило
    save('rules/rule_air_restored.json', RULE_AIR_BACK)
    man = load('manifest.json')
    if 'rule_air_restored.json' not in man['rules']:
        man['rules'].append('rule_air_restored.json')
        man['rules'].sort()
        save('manifest.json', man)

    # 5. предметы
    for iid, snds in ITEM_SOUNDS.items():
        p = f'entities/{iid}.json'
        e = load(p)
        s = e.get('sounds') or {}
        s.update(snds)
        e['sounds'] = s
        save(p, e)

    # 6. реплики: ink + конструктор
    for name, start, snd in LINES:
        p = f'dialogues/{name}.ink'
        lines = open(os.path.join(ROOT, p), encoding='utf-8').read().split('\n')
        hit = 0
        for i, line in enumerate(lines):
            body = line.strip()
            if body.startswith(start) and '# sfx:' not in line:
                lines[i] = line.rstrip() + ' # sfx: ' + snd
                hit += 1
        with open(os.path.join(ROOT, p), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines))
        # конструктор
        p = f'dialogues/{name}.dlg.json'
        d = load(p)
        cnt = 0

        def scan(secs):
            nonlocal cnt
            for sec in secs:
                for st in sec.get('steps', []):
                    l = st.get('line')
                    if l and l.get('text', '').strip().startswith(start) and not l.get('sfx'):
                        l['sfx'] = snd
                        cnt += 1

        for n in d.get('nodes', []):
            scan(n.get('sections') or [])
            for ch in n.get('choices', []):
                scan(ch.get('sections') or [])
        save(p, d)
        print(f'  {name}: ink {hit}, конструктор {cnt} — {snd}')

    print('\nготово')


if __name__ == '__main__':
    main()
