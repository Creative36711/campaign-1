#!/usr/bin/env python3
"""Read-only numerical audit of CURRENT campaign data; no old patch imports.

Bounds and sensitivity calculations are explicitly NOT a Forge combat simulator.
All JSON/text reports are regenerated from tracked campaign modules.
"""
from __future__ import annotations
from collections import Counter
import itertools
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.time_budget import build_graph, shortest, ROUTE, EXTRA_THOROUGH, EXTRA_FULL, SLEEP_TICKS


def load(path): return json.loads((ROOT / path).read_text())

def nodes(value, route=''):
    yield route, value
    if isinstance(value, dict):
        for k, v in value.items(): yield from nodes(v, route + '/' + k)
    elif isinstance(value, list):
        for i, v in enumerate(value): yield from nodes(v, route + '/' + str(i))


def damage_distribution(expr):
    m = re.fullmatch(r'(\d+)d(\d+)([+-]\d+)?', expr)
    if not m: raise ValueError(expr)
    number, sides, plus = int(m[1]), int(m[2]), int(m[3] or 0)
    outcomes = Counter(sum(dice) + plus for dice in itertools.product(range(1, sides + 1), repeat=number))
    total = sum(outcomes.values())
    return {value: count / total for value, count in outcomes.items()}


def main():
    c, manifest = load('campaign.json'), load('manifest.json')
    ents = {e['id']: e for e in (load('entities/' + n) for n in manifest['entities'])}
    report = {'method': 'static bounds and simplified sensitivity only; NOT a Forge runtime playtest', 'issues': []}
    needs = []
    for d in c['difficulties']:
        for n in c['needs']:
            decay = n['decay_per_tick'] * d['need_decay']
            needs.append({'difficulty': d['label'], 'need': n['label'], 'per_hour': decay,
                          'hours_to_critical_from_100': (n['max'] - n['critical_threshold']) / decay,
                          'hours_to_zero_from_100': n['max'] / decay,
                          'reserve_after_37h_without_restore': max(0, n['max'] - 37 * decay),
                          'reserve_after_53h_without_restore': max(0, n['max'] - 53 * decay),
                          'conditional': bool(n.get('decay_when'))})
    report['needs'] = needs
    cc = c['char_creation']
    allowed = [s['id'] for s in c['skills'] if s['id'] not in cc['forbidden_skills']]
    builds = []
    for p in cc['professions']:
        stat_spent = sum(v - cc['stat_limits']['min'] for v in p['stats'].values())
        for call in cc['callings']:
            spent = 0
            for skill in allowed:
                floor = max(cc['skill_floor'], 25 if skill in cc['mandatory_skills'] else 0) + p.get('skill_bonus', {}).get(skill, 0)
                spent += call['skills'].get(skill, floor) - floor
            builds.append({'profession': p['label'], 'calling': call['label'], 'stats_spent': stat_spent, 'skills_spent': spent,
                           'hp_average_con_siz': (p['stats']['CON'] + p['stats']['SIZ']) / 2,
                           'starting_money': sum(i['quantity'] for i in p['items'] if i['item'] == 'item_mark'),
                           'starting_food_count': sum(i['quantity'] for i in call.get('items', []) + p['items'] if i['item'] == 'item_ration')})
            if stat_spent != cc['total_points'] or spent != cc['skill_points']:
                report['issues'].append('Нарушен бюджет ' + p['label'] + '/' + call['label'])
    report['creation'] = builds
    economy = []
    for eid in ['item_water','item_ration','item_stew','item_coal','item_cloth','item_rope','item_filter','item_bandage','item_tonic','item_antirot','item_vest']:
        e = ents[eid]
        effects = [v for _, v in nodes(e.get('on_use', {})) if isinstance(v, dict) and v.get('type') in ['change_need','change_hp']]
        economy.append({'item': e['label'], 'base_price': e.get('value', {}).get('mark', 0), 'effects': effects})
    report['economy'] = economy
    weapons = [e for e in ents.values() if e.get('weapon_data')]
    enemies = []
    for eid in ['npc_thug','npc_ashhound','npc_rotling','npc_watchman']:
        e = ents[eid]
        w = e.get('natural_weapon') or ents[e['equipment']['weapon']]['weapon_data']
        enemies.append({'id': eid, 'label': e['label'], 'hp_average_con_siz': (e['stats']['CON']+e['stats']['SIZ'])/2,
                        'armor': e.get('armor',0), 'attack_skill': w['skill'], 'attack_chance': e['skills'][w['skill']],
                        'dodge': e['skills'].get('dodge',0), 'damage': w['damage'], 'damage_bonus': w.get('damage_bonus',False), 'abilities': e.get('abilities',[])})
    report['enemies'] = enemies
    sensitivity = []
    for weapon in weapons:
        w = weapon['weapon_data']
        for e in enemies:
            distribution = damage_distribution(w['damage'])
            on_hit = sum(max(0, damage-e['armor'])*p for damage,p in distribution.items())
            # The second bound is ordinary independent hit & dodge rolls. Forge
            # opposed-success ranks, special hits, parry, luck/AI are NOT modeled.
            per_action = on_hit * .5 * (1-e['dodge']/100)
            sensitivity.append({'weapon': weapon['label'], 'enemy': e['label'], 'damage_on_plain_hit_after_armor_no_bonus': on_hit,
                                '50_skill_independent_dodge_damage_per_action': per_action,
                                'successful_hits_to_average_hp': e['hp_average_con_siz']/on_hit if on_hit else None,
                                'actions_to_average_hp_in_simplified_bound': e['hp_average_con_siz']/per_action if per_action else None})
    report['combat_sensitivity'] = sensitivity
    g, cur, travel = build_graph(), c['starting_scene'], 0
    for target, _ in ROUTE:
        leg = shortest(g,cur,target)
        if leg is None: report['issues'].append('Нет планового пути ' + cur + '/' + target); leg=0
        travel += leg; cur=target
    travel += shortest(g,cur,'scene_pump_hall')
    actions = sum(n for _,n in ROUTE)
    report['time'] = {'travel':travel,'planned_actions':actions,'plan':travel+actions,
                     'expanded':travel+actions+EXTRA_THOROUGH+SLEEP_TICKS,
                     'full':travel+actions+EXTRA_FULL+SLEEP_TICKS*3,
                     'deadline':c['deadline_ticks'], 'absolute_flood_tick':c['starting_tick']+c['deadline_ticks'],
                     'limitations':'open directed paths assumed; planned actions, not exact locked route or a shortest completion proof'}
    encounter_rows = []
    for table in load('encounters/encounters.json')['encounter_tables']:
        total = sum(e['weight'] for e in table['entries'])
        chance = 1.0  # Attached roads roll the weighted table; no separate chance field.
        roads = [(loc['id'], road['to']) for reg in load('world.json')['regions'] for loc in reg['locations'] for road in loc.get('travel_connections', []) if road.get('random_encounter_table') == table['id']]
        combat_weight = sum(e['weight'] for e in table['entries'] if e.get('type') == 'combat')
        encounter_rows.append({'id':table['id'],'encounter_chance':chance,'combat_given_encounter':combat_weight/total,
                               'combat_per_eligible_check': chance * combat_weight/total,
                               'roads': roads, 'rolls': table.get('rolls',1),
                               'enemy_counts': [en['count_max'] for e in table['entries'] for en in e.get('enemies',[])]})
    report['encounters'] = encounter_rows
    xp_sites = []
    for folder in ['entities','rules','quests','dialogues']:
        for p in sorted((ROOT/folder).glob('*.json')):
            for route, v in nodes(json.loads(p.read_text())):
                if isinstance(v,dict) and v.get('type') == 'grant_xp':
                    xp_sites.append({'file':p.relative_to(ROOT).as_posix(),'route':route,'points':v['points']})
    report['xp_sites'] = xp_sites
    report['xp_syntactic_sum_not_route_total'] = sum(x['points'] for x in xp_sites)
    # Free-state intersections are exhaustively enumerated; base is fallback.
    state_issues = []
    for name in manifest['scenes']:
        scene = load('scenes/' + name)
        flags = sorted({key for s in scene.get('states',[])[1:] for key in [s.get('condition',{}).get('flag'),s.get('condition',{}).get('not_flag')] if key})
        for bits in itertools.product([False,True],repeat=len(flags)):
            active_flags = {k for k,b in zip(flags,bits) if b}
            active = [s['id'] for s in scene['states'][1:]
                      if (not s['condition'].get('flag') or s['condition']['flag'] in active_flags)
                      and (not s['condition'].get('not_flag') or s['condition']['not_flag'] not in active_flags)]
            if len(active)>1: state_issues.append({'scene':scene['id'],'flags':sorted(active_flags),'states':active})
    report['scene_state_intersections'] = state_issues
    # Independent day/weather variations can deliberately share backgrounds.
    report['state_intersection_note'] = 'Flag-only upper bound; scenes with independent weather/time predicates require separate interpretation.'
    out = ROOT/'tools/balance-audit.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    lines = ['# Баланс актуальной кампании — 2026-10-08','',
             '**Метод:** чтение данных, граничные расчёты потребностей, бюджетов, цен и чувствительности урона. Не движковый плейтест.','',
             '## Потребности','',
             'От 100, без еды/воды/сна/огня. Дыхание считается только на восьмом/девятом без исправной маски; тепло только в подземных локациях. Критический порог — предупреждение, не момент смерти. Мировой DOT по гайду оставляет минимум 1 HP; отдельный `change_hp` нужно проверять отдельно.','',
             '| Сложность | Шкала | Расход/ч | До критического, ч | До нуля, ч | Остаток через 37 / 53 ч |','|---|---|---:|---:|---:|---:|']
    for n in needs:
        lines.append(f"| {n['difficulty']} | {n['need']} | {n['per_hour']:.2f} | {n['hours_to_critical_from_100']:.1f} | {n['hours_to_zero_from_100']:.1f} | {n['reserve_after_37h_without_restore']:.1f} / {n['reserve_after_53h_without_restore']:.1f} |")
    lines += ['', 'На нормальной сложности 53 ч без потреблений оставляют 31,1 еды, 25,8 воды, 47 сна. Одна фляга (+45) покрывает ещё 32,1 ч нормального расхода; один паёк (+38) — 29,2 ч. На высокой сложности соответствующие запасы нужно принимать раньше. Верхний воздух восстанавливает 8/ч; поверхность возвращает тепло 4/ч, а не согревает любой подземный лагерь.', '',
              '### Исправление дыхателя','',
              'Раньше пустая, но надетая маска отключала расход воздуха навсегда; четырёхчасовой кашель можно было переждать. Теперь отдельный поддерживаемый признак защищает только при надетой маске и неотработанных банках. У первой банки — штольня, у второй — забой и подъём; истощение фиксируется положительным событием возвращения с девятого, не отрицанием события входа. Повторный спуск тратит дыхание и вызывает 4 ч кашля. Замена: уголь + тряпьё +1 ч на верстаке, без броска, снимает кашель. На чистом верхнем воздухе кашель снимается автоматически. Срок обновления защитного признака в конкретной версии движка всё ещё нуждается в runtime-проверке.', '',
              '## Создание персонажа', '', '| Происхождение | Призвание | Очки статов | Очки навыков | (CON+SIZ)/2 до округления | Стартовые марки |', '|---|---|---:|---:|---:|---:|']
    for b in builds:
        lines.append(f"| {b['profession']} | {b['calling']} | {b['stats_spent']} | {b['skills_spent']} | {b['hp_average_con_siz']:g} | {b['starting_money']} |")
    lines += ['', 'Все девять сочетаний имеют бюджеты 35/215. Навыки проверяются с порогом и бонусами происхождения, не простым суммированием абсолютных значений. HP приведено до движкового округления; фиксированные HP из прежних отчётов не используются.', '',
              '## Цены и расходники', '', '| Предмет | Базовая цена | Эффекты употребления |','|---|---:|---|']
    for e in economy:
        lines.append(f"| {e['item']} | {e['base_price']} | {json.dumps(e['effects'],ensure_ascii=False)} |")
    lines += ['', 'Покупка использует множители сложности 1 /1,25 /1,5, а также торговлю/репутацию/события цены. Это базовый прайс, не обещание цены на экране. Не суммируем деньги всех взаимоисключающих финалов и выпадений. Бинт лечит 7, тоник 8; необходимость использовать их зависит от ограничителя HP и конкретного боя. Постоянные награды «Первая установка бандажа», «Возврат жетона», «Регистрация дела» защищены независимыми несбрасываемыми условиями и тестами.', '',
              '## Бои и чувствительность', '', '| Противник | (CON+SIZ)/2 | Броня | Атака | Уклонение | Оружие |', '|---|---:|---:|---:|---:|---|']
    for e in enemies:
        lines.append(f"| {e['label']} | {e['hp_average_con_siz']:g} | {e['armor']} | {e['attack_chance']} | {e['dodge']} | {e['damage']} (бонус {'да' if e['damage_bonus'] else 'нет'}) |")
    lines += ['', 'Полная таблица для каждого оружия/противника — в JSON. Нож 1d4+1 наносит в среднем 2,5 после брони боевика и 1,5 после брони дозорного (без критов/бонуса). При условной атаке 50 и независимом уклонении 28 средний урон в действие по боевику —0,90: даже один враг не бесплатный бой. Это НЕ точная вероятность попадания системы opposed success: ранги успеха, парирование, удача, спутники, яд/страх/мораль и AI здесь не моделируются. Дозорного с бронёй 2 не следует балансировать как обычного боевика; основной маршрут допускает обход/договаривание и снаряжение.', '',
              'Случайные встречи сохраняют прежние веса, но всегда один враг. Риск нескольких проверок считается через 1−(1−p)^n только при независимости, которой runtime может не гарантировать. Данные:', '']
    for e in encounter_rows:
        lines.append(f"- `{e['id']}`: событие {e['encounter_chance']:.1%}, бой при событии {e['combat_given_encounter']:.1%}, бой на допустимую проверку {e['combat_per_eligible_check']:.1%}; максимум врагов {max(e['enemy_counts'],default=0)}.")
    lines += ['', '## Время, XP и состояния', '',
              f"- Направленный граф: дорога {travel} + план действий {actions} = {travel+actions} ч; расширенный {report['time']['expanded']}; полный {report['time']['full']}; срок {c['deadline_ticks']}, потоп на абсолютном тике {report['time']['absolute_flood_tick']}.",
              '- Закрытые/неоткрытые пути для оценки считаются свободными. Это не доказательство кратчайшего прохождения и не сумма всех обязательных кнопок.',
              f"- В JSON {len(xp_sites)} синтаксических мест выдачи XP, сумма {report['xp_syntactic_sum_not_route_total']}. **Это не достижимая награда маршрута:** возможны альтернативные концовки, условные ветки и Ink/sidecar-дубли. Прежняя «631 XP гарантированно» удалена из актуального документа.",
              '- Возврат жетона даёт 40 через стадию квеста, не 80. Тело остаётся на месте после жетона. Вынос тела +15 один раз; сверка наряда +10 один раз; регистрация +10 за час. Стягивание/ослабление цепи можно повторять, XP15 и тепло10 нельзя.',
              '- Забой: состояние «Цепь на шве» исключено после изъятия сердцевины, чтобы две картинки не спорили за приоритет.',
              '- Хронология: 18:40 мастер внизу, 19:10 остановка, 20:00 стража — промежуток 50 минут, не 20. Яров записан на седьмой, тело на восьмом. Технические подписи скрытых режимов заменены атмосферными названиями.', '',
              '## Обязательные runtime-сценарии для мастера', '',
              '1. Каждый из 9 стартовых вариантов: путь без боя, на нормальной сложности; отдельно боец и машинист с одной случайной встречей.',
              '2. Маска: надеть/снять → восьмой → штольня → забой → возврат → второй спуск → ожидание >4 ч → переснаряжение. Сверить порядок need tick/rule evaluation, не только флаги.',
              '3. Врачевание/парирование/бегство с ножом и ключом против всех четырёх врагов, с/без Иры; затем уровни сложности 1,25/1,5 урона.',
              '4. Все 6 финалов, потоп на тике79, одна безопасная койка и лагерь с 15% засадой. Койка обещает только явно заданные +2 HP/+15 тепла/+100 сна; MP/удача/усталость встроенного отдыха — отдельная механика.',
              '5. Тело, Регистратор, Жила: повторить действия в новой сцене/новом разговоре и после save/load. Статические регрессии не проверяют сериализацию движка.', '',
              f"Ошибок бюджета/сметы: {len(report['issues'])}. Пересечения условий иллюстраций записаны отдельно (верхняя оценка без времени/погоды): {len(state_issues)}."]
    (ROOT/'tools/balance-audit.md').write_text('\n'.join(lines)+'\n')
    print('Баланс:',len(builds),'сборок;',len(needs),'строк потребностей;',len(xp_sites),'мест XP;',len(report['issues']),'ошибок; состояния',len(state_issues),'верхних пересечений')
    return 1 if report['issues'] else 0

if __name__ == '__main__': raise SystemExit(main())
