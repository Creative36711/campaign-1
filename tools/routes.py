"""Маршруты для tools/route_sim.py: по одному на каждую концовку и вариант «Тишины».
Шаги: ('go', scene) · ('use', entity, подстрока опции, {rolls:[...], combat:'victory'|'defeat', dlg:[[...]]})
· ('talk', npc, [подстроки реплик], {knot, present, rolls}) · ('buy', npc, item, qty) · ('craft', recipe) · ('wait', ticks).
Броски без явного rolls считаются успешными; каждый бросок попадает в список рисков маршрута."""

# общий отрезок: ключ с привода, клапан, затвор, дело №136 (открывает девятый ярус)
CORE = [
    ('go', 'scene_gate_hall'),
    ('go', 'scene_pump_hall'),
    ('use', 'item_pump_engine', 'Снять с привода ключ'),
    ('go', 'scene_pump_shaft'),
    ('use', 'item_ladder', 'Спуститься по скобам'),
    ('use', 'item_niche', 'Обыскать нишу'),
    ('go', 'scene_flood_gallery'),
    ('go', 'scene_sluice'),
    ('use', 'item_sluice_mech', 'Установить клапан'),
    ('go', 'scene_office'),
    ('go', 'scene_archive'),
    ('use', 'item_shelf', 'Прочитать дело №136'),
]
RESH_CORE = [('go', 'scene_face'), ('talk', 'npc_resh', ['Затвор держит. Теперь отдай сердцевину.'])]
# заряд: доверие Реша → рецепт → лом и масло у Дожа → скамья в Сухом ряду
TRUST = [('go', 'scene_face'),
         ('talk', 'npc_resh', ['Почему ты спустился вниз?', 'Научи собирать заряд.', 'Затвор держит. Теперь отдай сердцевину.'])]
CHARGE = TRUST + [  # лом покупается у Дожа
    ('go', 'scene_dry_row'), ('buy', 'npc_dozh', 'item_scrap', 2), ('buy', 'npc_dozh', 'item_oil', 1),
    ('craft', 'recipe_charge'), ('go', 'scene_sluice')]
CHARGE_OWN = TRUST + [  # у мастера стартовые 2 лома
    ('go', 'scene_dry_row'), ('buy', 'npc_dozh', 'item_oil', 1), ('craft', 'recipe_charge'), ('go', 'scene_sluice')]
# лом без денег: ящик в шлюзе и нанос в галерее (броски сыска), карманы стража
SCAVENGE = [('go', 'scene_gate_hall'), ('use', 'item_crate', 'Обыскать ящик'),
            ('go', 'scene_flood_gallery'), ('use', 'item_debris', 'Разгрести нанос'),
            ('go', 'scene_sluice'), ('use', 'item_dead_guard', 'Обыскать карманы')]
CHARGE_SCAV = TRUST + [
    ('go', 'scene_dry_row'), ('buy', 'npc_dozh', 'item_oil', 1), ('craft', 'recipe_charge'), ('go', 'scene_sluice')]


def R(prof, diff, expect, steps):
    return {'prof': prof, 'diff': diff, 'expect': expect, 'steps': steps}


ROUTES = {
    'pump_wright': R('prof_wright', 'diff_inspector', 'ending_pump', CORE + RESH_CORE + [
        ('go', 'scene_pump_hall'), ('use', 'item_pump_engine', 'Вставить сердцевину')]),
    'vein_inspector': R('prof_inspector', 'diff_deep', 'ending_vein', CORE + RESH_CORE + [
        ('talk', 'npc_vein', ['Вложить сердцевину в стену.'])]),
    'closed_inspector_lockpick': R('prof_inspector', 'diff_watchman', 'ending_closed', CORE + [
        ('go', 'scene_drift'), ('use', 'item_cache', 'Взломать крышку'),
        ('go', 'scene_office'), ('talk', 'npc_kast', ['Я нашёл гроссбух.', 'Отдать гроссбух и закрыть дело.'])]),
    'closed_key_from_resh': R('prof_wright', 'diff_deep', 'ending_closed', CORE + RESH_CORE + [
        ('go', 'scene_drift'), ('use', 'item_cache', 'Отпереть ключом'),
        ('go', 'scene_office'), ('talk', 'npc_kast', ['Я нашёл гроссбух.', 'Отдать гроссбух и закрыть дело.'])]),
    'silence_stood_inspector': R('prof_inspector', 'diff_inspector', 'ending_silence_stood', CORE + CHARGE + [
        ('use', 'item_sluice_mech', 'Заложить заряд', {'rolls': [True]})]),
    'silence_kell_inspector_deep': R('prof_inspector', 'diff_deep', 'ending_silence_kell', CORE + SCAVENGE + CHARGE_SCAV + [
        ('use', 'item_sluice_mech', 'Заложить заряд', {'rolls': [False], 'combat': 'victory'})]),
    'silence_rigged_wright': R('prof_wright', 'diff_watchman', 'ending_silence_rigged', CORE + CHARGE_OWN + [
        ('use', 'item_sluice_mech', 'Заложить заряд снизу, на замедлитель', {'rolls': [True]})]),
    'death_at_sluice': R('prof_inspector', 'diff_inspector', 'ending_death', CORE + CHARGE + [
        ('use', 'item_sluice_mech', 'Заложить заряд', {'rolls': [False], 'combat': 'defeat'})]),
    'flood_deadline': R('prof_inspector', 'diff_inspector', 'ending_flood', [('go', 'scene_gate_hall'), ('wait', 80)]),
    # «Тишина» без Келла: завиток на квитанциях → Каст снимает режим и караул у затвора
    'silence_plain_investigator': R('prof_inspector', 'diff_watchman', 'ending_silence', CORE + [
        ('go', 'scene_pump_hall'), ('use', 'item_resh_door', 'Взломать замок'),
        ('go', 'scene_pump_room'), ('use', 'item_locker', 'Вскрыть шкафчик'),
        ('go', 'scene_archive'), ('talk', 'npc_registrar', ['Наряд стражи за ночь тринадцатого.']),
        ('go', 'scene_flood_gallery'), ('talk', 'npc_glazier', ['Кому ты его несёшь?']),
        ('go', 'scene_gate_office'), ('use', 'item_case', 'Сличить завиток'),
        ('go', 'scene_office'), ('talk', 'npc_kast', ['Тот же завиток']),
        ('go', 'scene_face'), ('talk', 'npc_resh', ['Почему ты спустился вниз?', 'Научи собирать заряд.']),
        ('go', 'scene_drift'), ('use', 'item_cache', 'Отпереть ключом'),
    ] + SCAVENGE + [
        ('go', 'scene_dry_row'), ('buy', 'npc_dozh', 'item_oil', 1), ('craft', 'recipe_charge'),
        ('go', 'scene_sluice'), ('use', 'item_sluice_mech', 'Заложить заряд у пустого затвора')]),
}
