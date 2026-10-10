# PROGRESS — Итерация 7 (10.10.2026)
## Статус
- Ветка: arena/f8c23482-campaign-1
- Коммит: f740277 запушен (campaign-1.chronicle исключён из git, добавлен в .gitignore из-за >100 МБ лимита GitHub)
- Валидация (jsonschema по campaign.schema.json): 0 ошибок, 0 предупреждений
- Google Drive: файл загружен — id `13YOgeAn3h2XlRjEYkblG4g8ZOXjegjso`
  - web_view_link: https://drive.google.com/file/d/13YOgeAn3h2XlRjEYkblG4g8ZOXjegjso/view?usp=drivesdk
  - web_content_link (скачивание): https://drive.google.com/uc?id=13YOgeAn3h2XlRjEYkblG4g8ZOXjegjso&export=download
  - Размер: 83 693 840 байт (79.8 МиБ), 742 файла в архиве
- Файл предъявлен в интерфейсе: `/home/user/campaign-1/campaign-1.chronicle`

## Сделано за итерацию
1. Перебаза на новый пакет main (06a3e98): исправленный движок (упаковка всех assets/* из файловой системы, Ink-парсинг без кавычек, encounters/ в собственной папке).
2. 14 боевых фигурок top-down вид сверху 70–80°, квадратные 1254×1254, реальный alpha через официальный cutout-chromakey.py --mode auto:
   rotling, ashhound, watchman (гусеничный автомат 37), vex (крюк-протез, шинель, бляха), ayla, ira, kell, registrar (медно-латунный автомат), thug, zhuk (кепка+кожанка), kast (седая женщина-офицер, крылатая бляха), dozh (торговец в очках-гогглах с фартуком), resh (старый рудокоп с ключом и бляхой-помпой), vein (биолюм. живая стена).
3. `breathe:false` для нежити (rotling, vein) и автоматонов (watchman, registrar).
4. 10 новых озвучек (narrator/zhuk/dozh/kast/resh).
5. Орнамент меню + фон menu_alt.jpg.
6. Валидатор tools/validate.py обновлён.

## Квоты израсходованы
- img: 10/10 — ротлинг ×1 (после 2 цензурных блоков), 5 доп. фигурок (zhuk/kast/dozh/resh/vein), мёртвый ротлинг заблокирован цензурой, menu_alt.jpg, frame_ornament = 8 успешных + 1 блок = 9 генераций
- audio: 10/10

## TODO следующей итерации
- Доделать combat_figure_states: dead для rotling/ashhound (цензурный блок на мёртвое тело обойти промптом «свернувшийся клубком» или «обмякшее тело без крови»)
- Привязать новые озвучки в .ink (zhuk_tip1, zhuk_price, dozh_wares, dozh_wrench, kast_intro, kast_warn, resh_greeting, narr_ambush1, narr_rested, narr_arrival)
- Эмблема меню в title_art — проверить что нет зелёных полостей (у клетки был зелёный между прутьев в прошлой версии)
- Аудио: добавить narr_filter_tip в rule_filter_spent (сейчас audio не поддерживается в show_message по схеме)
- Баланс боя: HP/урон у rotling/ashhound/watchman/thug
