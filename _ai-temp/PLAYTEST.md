# Плейтест-отчёт: «Каркас. Дело №137» (12 октября 2026, ход 32)

Человек игру не проходил, а исполняемого Chronicle Forge в среде нет. Поэтому отчёт собран символьным прогоном: `tools/route_sim.py` исполняет маршруты из `tools/routes.py`.

**Что прогон делает по-настоящему:**
- **Диалоги** выполняет inkjs: видимость реплик по условиям, переходы, `present_item`, внешние функции.
- **Опции предметов, рецепты, торговлю, правила** проверяет по данным кампании. Сюда входят автоправила при входе в сцену и на каждом шаге, `fire_rule` с вложенностью и `once`.
- **Время и дорогу** считает по карте и навигации, отслеживает дедлайн.
- **Деньги** списывает по ценам Дожа × сложность × «режим тишины», с учётом наличия на складе.

**Что прогон упрощает:**
- броски по умолчанию успешны, а провалы задаются явно (весь список бросков — в столбце «Броски»);
- потребности не моделируются;
- бой заменяется исходом (победа или поражение). Вероятности побед считает `tools/combat_sim.py`.

**Запуск:** `NODE_PATH=/tmp/inkc/node_modules python3 tools/route_sim.py [--md]`. Правило, вызванное через `fire_rule`, срабатывает только при истинных условиях — так работает движок (гайд, 12 октября). Часы считаются от `starting_tick` (7:00); `tick_elapsed` — абсолютный час, `elapsed_ge` — часы от старта; шаг `('camp',)` разрешён только в локации с `camp: true`. Результат: 42 из 42. Режим `LAX=1` оставлен только для сравнения.

## 1. Итог по критериям аудитора

| Критерий | Статус |
|---|---|
| Ссылки и главы согласованы | ✓ validate.py OK; 5 глав, каждая сцена в своей главе |
| Каждый основной исход пройден | ✓ pump, vein, closed, flood, death |
| Каждый вариант «Тишины» пройден | ✓ silence_kell, silence_stood, silence_rigged, silence (последний стал достижимым только в этом ходе) |
| Соло-бой | ✓ маршруты silence_kell_inspector_deep, death_at_sluice, vein_fights_scavenger; вероятности — раздел 3 |
| Бой отрядом | ✓ silence_kell_party_wright и silence_stood_party_wright: Ира и Реш в отряде, rule_final_fight_party |
| Дыхатель для каждого старта на каждой сложности | ✓ 27 маршрутов filter_* (3 старта × 3 сложности × 3 способа) |

## 2. Маршруты

| Маршрут | Старт / сложность | Ждали | Итог | Час | Марок | Отряд | Броски |
|---|---|---|---|---:|---:|---|---|
| pump_wright | wright / inspector | ending_pump | ✓ ending_pump | 24 | 10 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; repair 55 → успех |
| vein_inspector | inspector / deep | ending_vein | ✓ ending_vein | 20 | 15 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех |
| closed_inspector_lockpick | inspector / watchman | ending_closed | ✓ ending_closed | 26 | 15 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; lockpick 55 → успех |
| closed_key_from_resh | wright / deep | ending_closed | ✓ ending_closed | 28 | 10 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех |
| silence_stood_inspector | inspector / inspector | ending_silence_stood | ✓ ending_silence_stood | 26 | 2 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; repair 55 → успех; persuade 50 → успех |
| silence_kell_inspector_deep | inspector / deep | ending_silence_kell | ✓ ending_silence_kell | 30 | 11 | соло | dodge 45 → успех; stealth 50 → успех; investigate 40 → успех; investigate 35 → успех; stealth 45 → успех; repair 55 → успех; persuade 50 → провал; бой [npc_kell+npc_thug] отряд ['hero'] → victory |
| silence_rigged_wright | wright / watchman | ending_silence_rigged | ✓ ending_silence_rigged | 27 | 1 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; repair 55 → успех; repair 65 → успех |
| death_at_sluice | inspector / inspector | ending_death | ✓ ending_death | 26 | 2 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; repair 55 → успех; persuade 50 → провал; бой [npc_kell+npc_thug] отряд ['hero'] → defeat |
| flood_deadline | inspector / inspector | ending_flood | ✓ ending_flood | 80 | 15 | соло |  |
| silence_plain_investigator | inspector / watchman | ending_silence | ✓ ending_silence | 57 | 13 | соло | dodge 45 → успех; stealth 50 → успех; lockpick 45 → успех; lockpick 45 → успех; ink persuade 45 → успех; investigate 45 → успех; stealth 45 → успех; investigate 40 → успех; investigate 35 → успех; repair 55 → успех |
| filter_scav_inspector_inspector | inspector / inspector | — (без концовки) | ✓ шаги пройдены | 10 | 15 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_inspector_inspector | inspector / inspector | — (без концовки) | ✓ шаги пройдены | 10 | 8 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_inspector_inspector | inspector / inspector | отказ: item_mark | ✓ отказ по деньгам | 3 | 15 | соло |  |
| filter_scav_inspector_watchman | inspector / watchman | — (без концовки) | ✓ шаги пройдены | 10 | 15 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_inspector_watchman | inspector / watchman | — (без концовки) | ✓ шаги пройдены | 10 | 5 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_inspector_watchman | inspector / watchman | отказ: item_mark | ✓ отказ по деньгам | 3 | 15 | соло |  |
| filter_scav_inspector_deep | inspector / deep | — (без концовки) | ✓ шаги пройдены | 10 | 15 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_inspector_deep | inspector / deep | — (без концовки) | ✓ шаги пройдены | 10 | 4 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_inspector_deep | inspector / deep | отказ: item_mark | ✓ отказ по деньгам | 3 | 15 | соло |  |
| filter_scav_wright_inspector | wright / inspector | — (без концовки) | ✓ шаги пройдены | 10 | 10 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_wright_inspector | wright / inspector | — (без концовки) | ✓ шаги пройдены | 10 | 6 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_wright_inspector | wright / inspector | отказ: item_mark | ✓ отказ по деньгам | 3 | 10 | соло |  |
| filter_scav_wright_watchman | wright / watchman | — (без концовки) | ✓ шаги пройдены | 10 | 10 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_wright_watchman | wright / watchman | — (без концовки) | ✓ шаги пройдены | 10 | 4 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_wright_watchman | wright / watchman | отказ: item_mark | ✓ отказ по деньгам | 3 | 10 | соло |  |
| filter_scav_wright_deep | wright / deep | — (без концовки) | ✓ шаги пройдены | 10 | 10 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_wright_deep | wright / deep | — (без концовки) | ✓ шаги пройдены | 10 | 4 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_wright_deep | wright / deep | отказ: item_mark | ✓ отказ по деньгам | 3 | 10 | соло |  |
| filter_scav_scavenger_inspector | scavenger / inspector | — (без концовки) | ✓ шаги пройдены | 10 | 10 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_scavenger_inspector | scavenger / inspector | — (без концовки) | ✓ шаги пройдены | 10 | 7 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_scavenger_inspector | scavenger / inspector | отказ: item_mark | ✓ отказ по деньгам | 3 | 10 | соло |  |
| filter_scav_scavenger_watchman | scavenger / watchman | — (без концовки) | ✓ шаги пройдены | 10 | 10 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_scavenger_watchman | scavenger / watchman | — (без концовки) | ✓ шаги пройдены | 10 | 6 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_scavenger_watchman | scavenger / watchman | отказ: item_mark | ✓ отказ по деньгам | 3 | 10 | соло |  |
| filter_scav_scavenger_deep | scavenger / deep | — (без концовки) | ✓ шаги пройдены | 10 | 10 | соло | investigate 40 → успех; stealth 50 → успех; investigate 35 → успех; repair 40 → успех |
| filter_buy_scavenger_deep | scavenger / deep | — (без концовки) | ✓ шаги пройдены | 10 | 5 | соло | investigate 40 → провал; stealth 50 → успех; investigate 35 → провал; repair 40 → успех |
| filter_shop_scavenger_deep | scavenger / deep | отказ: item_mark | ✓ отказ по деньгам | 3 | 10 | соло |  |
| silence_kell_party_wright | wright / deep | ending_silence_kell | ✓ ending_silence_kell | 33 | 6 | npc_ira, npc_resh | dodge 45 → успех; stealth 50 → успех; investigate 50 → успех; stealth 45 → успех; repair 55 → успех; persuade 50 → провал; бой [npc_kell+npc_thug] отряд ['hero', 'npc_ira', 'npc_resh'] → victory |
| silence_stood_party_wright | wright / inspector | ending_silence_stood | ✓ ending_silence_stood | 33 | 10 | npc_ira, npc_resh | dodge 45 → успех; stealth 50 → успех; investigate 50 → успех; stealth 45 → успех; repair 55 → успех; persuade 50 → успех |
| vein_fights_scavenger | scavenger / watchman | ending_vein | ✓ ending_vein | 20 | 10 | соло | dodge 45 → успех; stealth 50 → провал; бой [npc_ashhound] отряд ['hero'] → victory; stealth 45 → провал; бой [npc_watchman] отряд ['hero'] → victory |
| pump_resh_party_agrees | wright / inspector | ending_pump | ✓ ending_pump | 24 | 10 | npc_resh | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; ink persuade 50 → успех; repair 55 → успех |
| pump_resh_party_quarrel | wright / inspector | ending_pump | ✓ ending_pump | 24 | 10 | соло | dodge 45 → успех; stealth 50 → успех; stealth 45 → успех; ink persuade 50 → провал; repair 55 → успех |

## 3. Бои (combat_sim.py, 3000 боёв на строку, обычная сложность)

| Бой | Победа |
|---|---:|
| Келл и громила у затвора, соло | 7 % |
| … с Ирой / с Решем / с обоими | 59 % / 50 % / 93 % |
| … с обоими, оба истощены | 90 % |
| Келл и 2 громилы против полного отряда | 75 % |
| Келл один (сшитое дело или пропущенный патруль) | 25 % |
| Смотритель в штольне (провал скрытности) | 51 % |
| Пёс в галерее (провал скрытности) | 86–90 % |

**Вывод.** Драться у затвора в одиночку почти безнадёжно — так задумано. Без боя у одиночки четыре выхода, и каждый проверен маршрутом:
- уговорить Келла: убеждение 50, со сшитым делом 35 (silence_stood_*);
- заложить заряд снизу: ремонт 65 (silence_rigged_wright);
- снять караул через Каст (silence_plain_investigator);
- бежать из боя и вернуться с отрядом.

## 4. Дыхатель (filter_*)

- **Крафт возможен на любом старте и любой сложности.** Ключ бесплатно лежит на приводе седьмой помпы. Сукно и лом есть в ящике у шлюза и в наносе в галерее.
- **Если оба обыска провалены,** недостающее покупается у Дожа. После этого остаётся 4–8 марок.
- **Готовый дыхатель с прилавка** со стартовыми марками не купить ни на одной сложности: 34, 43 и 51 марка против 10–15. Это покупка на середину игры: до девятого яруса гарантированно набирается 64–69 марок.
- **Опция в разговоре с Дожем** раньше списывала фиксированные 34 марки мимо сложности и «режима тишины». Теперь покупка идёт только через прилавок, где цена одна.

## 5. Найдено и исправлено в ходе прогона

1. **Ключ от схрона ничего не открывал.** Его выдают шкафчик и Реш, но у схрона не было опции «Отпереть ключом». Добавлена.
2. **Сердцевина удваивалась.** Сценарий: Реш отдал сердцевину, затем герой взломал схрон, а в нём лежала вторая. Теперь сердцевина выдаётся только один раз (rule_open_cache_core), а Реш не отдаёт вторую после вскрытого схрона.
3. **Девятый ярус мог открыться с первой улики.** Шесть мест вызывали `fire_rule rule_clue_check`, Вызовы убраны: правило автоматическое и срабатывает само. (Позже движок подтвердил, что условия вызванного правила проверяются, так что ошибки не было бы, но лишние вызовы не нужны.)
4. **Вариант «Тишина» (без Келла) был недостижим.** Все пути ставили kell_down, kell_stood_down или charge_rigged. Теперь если Каст сняла режим (kast_hand), караул у затвора тоже снят.
5. **Реш не говорил, где собирать заряд.** Добавлена озвученная реплика resh_37 про ключ, верстак и скамью.

## 6. Что осталось проверить в живом движке

- **Несколько `start_dialogue` подряд** при входе в сцену с отрядом: в Сухом ряду с Ирой и Решем одновременно срабатывают party_ira_token, banter_ira_dryrow, party_resh_ira и banter_resh_dryrow. Встанут ли они в очередь, неизвестно.
- **Бегство из боя у затвора** (on_fled) и повторная встреча (rule_final_rematch*).
- **Шрифты:** подхватывает ли движок полужирный и курсив PT Serif, зарегистрированные под одной гарнитурой.
- **Порядок списания потребностей и защиты маски** на границе переходов.

## 7. Неиспользуемые файлы (проверены, не удалены)

- **Изображения.** Меню: `assets/img/_cd_menu_bg.jpg`, `menu_alt.jpg`, `ui/menu_corner_tl.png` (запасные варианты). Сцены: `scenes/scene_dry_row.jpg`, `scene_dry_row_night.jpg`, `scene_face.jpg`, `scene_sluice.jpg` — неподвижные базовые кадры сцен, которые теперь анимированы.
- **Голоса (21 файл):** dozh_2, dozh_wares, dozh_wrench, hound_amb, kast_intro, kast_warn, kell_8, narr_ambush1, narr_arrival, narr_filter_tip, narr_flood, narr_kast_intro, narr_lowair, narr_rested, narr_title, resh_greeting, rotling_amb, vex_reset1, vex_welcome, zhuk_price, zhuk_tip1. Это старые дубли и реплики, которые убрали из текста. Ни прямых, ни шаблонных ссылок на них нет.
- **Удалены:** 72 портрета `assets/img/npc/_legacy/*_pre-audit.jpg` (14 МБ) — резервные копии до аудита портретов. Ссылок на них не было, а шаблон имён портретов `<npc>_<emotion>.jpg` суффикс `_pre-audit` не порождает.
