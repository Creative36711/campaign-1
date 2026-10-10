# РЕЕСТР ГОЛОСОВ КАМПАНИИ (аудит 10.10.2026)

Источник истины по голосам. Обновлять после каждой переозвучки (вычёркивать из «Старый голос»).
Метод: эмбеддинги Resemblyzer (`tools/voice_audit.py voice`); «тот же голос» = близость ≥ 0.85 к эталону
(короткие реплики < 3 с дают 0.80–0.89 — это норма). Эмбеддинги-кэш: `_ai-temp/voice_emb.json` (не в git).
**`add_voice` НЕ вызывать** — только существующие voice-id ниже.

## Текущие голоса (voice-id этой сессии)

| voice-id | Кто говорит | Эталонные файлы |
|---|---|---|
| voice-01 | Айла | ayla_1–13 (все уже одним голосом) |
| voice-03 | Рассказчик (narr_*, intro_*, prologue_*, final_*, flood_*, rev_*) | narr_glazier_1–2, final_silence_3, narr_resh_3, narr_vex_3–4, narr_kast_8, narr_ira_9–11 |
| voice-04 | Реш **и** Дож (один голос на двоих — известное ограничение) | resh_2, 4, 11, 14–17; dozh_1, 8, 14–16 |
| voice-05 | Жук | zhuk_4, 6, 12, 14–19 (+ переозвучены 1, 2, 7, 11) |
| voice-06 | Векс | vex_1–20 — **ВЕСЬ Векс готов** |
| voice-07 | Ира **и** Каст (один голос на двоих) | ira_18–30; kast_18–21 |
| voice-08 | Стекольщик (Сыч) | glazier_1–7 |
| — | Келл, Регистратор, Жила | своего voice-id нет; каждый звучит одним (старым) голосом — НЕ переозвучивать |

## Старые голоса (больше не используются) и чьи файлы ими записаны

| Старый голос | Совпадает с | Файлы в нём |
|---|---|---|
| **СТАРЫЙ-РАССКАЗЧИК** | голос Келла (0.92) | 75 файлов рассказчика (список ниже) + все kell_1–15 (Келла оставляем) |
| **СТАРАЯ-ИРА** | похож на голос Жилы (0.84) и старой Каст (0.84) | ira_1–13, 15–17 (ira_14 уже voice-07) |
| **СТАРАЯ-КАСТ** | — | kast_1–17 (kast_12 — одно слово «Покажи.», голос не определить; переозвучить вместе со всеми) |
| **= voice-08 (стекольщик)** | старый Реш | resh_1, 3, 5, 6, 7, 8, 10, 12 (+ resh_greeting — сирота) |
| **СТАРЫЙ-ЖУК** | dozh_2, 3, 5, 6, 10 (0.97) | zhuk_3, 9, 10, 13 (1, 2, 11 уже переозвучены) |
| **СТАРЫЙ-ЖУК** | — | dozh_2, 3, 5, 6, 10 — Дож говорил голосом старого Жука |
| ~~= voice-08~~ | ~~vex_1, 3, 4~~ | **исправлено в итерации 16** |

Одним голосом изначально (не трогать): Айла (старые ≈ voice-01, 0.92), Келл, Регистратор, Жила, Стекольщик.
zhuk_5, zhuk_8 — уже voice-05 (0.91). resh_9, resh_13 — уже voice-04. dozh_4, 7, 9, 11, wares, wrench — уже voice-04.

## Рассказчик: ровно ДВА голоса

- **Новый голос рассказчика — один (voice-03)**: 16 подключённых файлов + 8 сирот.
  - подключены: final_silence_3, narr_dozh_4, narr_dozh_5, narr_glazier_1, narr_glazier_2, narr_ira_10, narr_ira_11, narr_ira_5, narr_ira_9, narr_kast_1, narr_kast_7, narr_kast_8, narr_resh_3, narr_vex_3, narr_vex_4, narr_zhuk_7
  - (narr_kast_1, narr_kast_7, narr_dozh_4, narr_ira_5 — короткие ремарки ~3 с, близость 0.82–0.89 к voice-03; третьего голоса нет)
  - сироты (не подключены нигде): narr_ambush1, narr_arrival, narr_filter_tip, narr_flood, narr_kast_intro, narr_lowair, narr_rested, narr_title
- **Старый голос рассказчика**: 75 подключённых файлов — ВСЕ на переозвучку voice-03:
  final_pump_1, final_pump_2, final_pump_3, final_silence_1, final_silence_2, final_vein_1, final_vein_2, final_vein_3, flood_1, flood_2, intro_archive_1, intro_archive_2, intro_drift_1, intro_drift_2, intro_dry_row_1, intro_dry_row_2, intro_face_1, intro_face_2, intro_flood_gallery_1, intro_flood_gallery_2, intro_gate_hall_1, intro_gate_hall_2, intro_gate_office_1, intro_gate_office_2, intro_office_1, intro_office_2, intro_pump_hall_1, intro_pump_hall_2, intro_pump_room_1, intro_pump_room_2, intro_pump_shaft_1, intro_pump_shaft_2, intro_sluice_1, intro_sluice_2, narr_ayla_1, narr_dozh_1, narr_dozh_2, narr_dozh_3, narr_ira_1, narr_ira_2, narr_ira_3, narr_ira_4, narr_ira_6, narr_ira_7, narr_ira_8, narr_kast_2, narr_kast_3, narr_kast_4, narr_kast_5, narr_kast_6, narr_kell_1, narr_kell_2, narr_kell_3, narr_kell_4, narr_kell_5, narr_registrar_1, narr_resh_1, narr_resh_2, narr_vein_1, narr_vein_2, narr_vein_3, narr_vex_1, narr_vex_2, narr_zhuk_1, narr_zhuk_2, narr_zhuk_3, narr_zhuk_4, narr_zhuk_5, narr_zhuk_6, prologue_1, prologue_2, prologue_3, rev_1, rev_2, rev_3

## ОЧЕРЕДЬ ПЕРЕОЗВУЧКИ (итого 125)

1. Жук (voice-05) — 4: zhuk_3, zhuk_9, zhuk_10, zhuk_13
2. Дож (voice-04) — 5: dozh_2, dozh_3, dozh_5, dozh_6, dozh_10
3. Реш (voice-04) — 8: resh_1, resh_3, resh_5, resh_6, resh_7, resh_8, resh_10, resh_12
4. Каст (voice-07) — 17: kast_1 … kast_17
5. Ира (voice-07) — 16: ira_1 … ira_13, ira_15, ira_16, ira_17
6. Рассказчик (voice-03) — 75: список выше (включая rev_1–3 из cutscene_revelation и flood_1 с дописанной фразой)

Порядок работы с каждым файлом: текст — из ink/JSON (`tools/voice_map.py`, для катсцен/сцен — поле `text` рядом с `voice`);
после генерации — `tools/voice_audit.py text <файлы>` и `tools/voice_audit.py voice <файлы>`; обновить этот реестр.

## Сироты (файлы есть, нигде не подключены; не переозвучивать без надобности)
dozh_wares, dozh_wrench, kast_intro, kast_warn, resh_greeting, vex_reset1, vex_welcome, zhuk_price, zhuk_tip1,
hound_amb, rotling_amb, narr_ambush1, narr_arrival, narr_filter_tip, narr_flood, narr_kast_intro, narr_lowair, narr_rested, narr_title
