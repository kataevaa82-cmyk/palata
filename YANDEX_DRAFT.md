# Черновик карточки Яндекс Игр

Подготовлено 30 августа 2026 года для версии `1.0.0`.

## 1. Технические параметры

- Архив: `build/Palata_0_Yandex.zip`
- Версия: `1.0.0`
- Платформы: `Десктоп`, `Мобильные → Android`
- `Мобильные → iOS`: включать только при наличии Apple Team ID — теперь это обязательное поле для iOS.
- ТВ: не выбирать, управление с пульта не реализовано.
- Ориентация: `Альбомная`.

## 2. Метаданные

- Игра переведена на: `Русский`, `Английский`.
- Возрастной рейтинг: `12+`.
  - Основание: стилизованная low-poly графика, нет крови, натуралистичных ран, оружия и шокирующей визуализации смерти.
  - Если в черновике или после проверки реального прохождения обнаружится более реалистичная демонстрация смерти, выбрать `16+`.
- Категории: `Хорроры`, `Симуляторы`.
- Теги: `3d`, `хоррор`, `мистика`, `выживание`, `от первого лица`, `на внимание`, `страшные`, `для подростков`, `десктоп`, `мобильные`.
- Ключевые слова: `хоррор,больница,ночная смена,аномалии,выживание,от первого лица,страшная игра`
- Игра использует облачные сохранения: `Да`.
- Отсроченная публикация: `Нет` после успешной проверки черновика на реальных устройствах.

### Комментарий разработчика

> Версия 1.0.0. Язык выбирается автоматически по i18n.lang при первом запуске; также есть ручной переключатель RU/EN. Облачное сохранение использует player.getData/player.setData, локальная копия остаётся для гостя. LoadingAPI.ready вызывается после полной готовности меню, GameplayAPI.start/stop отмечает фактический игровой процесс. Полноэкранная реклама через showFullscreenAdv показывается только в логических паузах; на время рекламы игра и звук останавливаются. Игра — стилизованный low-poly хоррор без крови, натуралистичных ран и оружия; смерть обозначается текстом и экраном результата. Поддерживаются desktop и touch, мобильная ориентация — альбомная. Внешних ссылок, покупок, rewarded-видео и баннеров нет.

## 3. Русская карточка

### Название

`Ночное дежурство: Палата 0`

### Описание для SEO

> Хоррор от первого лица о ночной смене в старой больнице. Выполняйте назначения, замечайте аномалии и доживите до рассвета!

### Об игре

> Вы — дежурный санитар в старой больнице. Сверяйте журнал и браслеты пациентов, выполняйте медицинские назначения и следите, чтобы отделение дожило до 06:00. В игре 11 ночных смен: отключение света, карантин, переливание, побег пациента, пожар, операция и другие истории. Привычные коридоры постепенно меняются, а среди пациентов и сотрудников появляются опасные аномалии. Исследуйте больницу от первого лица, пользуйтесь фонариком, замечайте несоответствия и сохраняйте рассудок. Прогресс сохраняется между запусками. Доступны русский и английский языки, управление с клавиатуры и сенсорного экрана.

### Короткое описание

> Проведите одиннадцать ночей в больнице, которая не спит.

### Как играть

> Выберите смену и начните дежурство. Читайте журнал и доску назначений, отвечайте на звонки, находите нужные предметы, проверяйте браслеты пациентов и выполняйте обязательные задачи до 06:00. Избегайте опасных аномалий и следите за здоровьем и рассудком. На компьютере: WASD — движение, мышь — обзор, E — действие, F — фонарик, Esc — пауза. На телефоне: левый стик — движение, свайп справа — обзор, кнопки «Действие», «Фонарик» и пауза.

## 4. English card

### Title

`Night Duty: Room 0`

### SEO description

> First-person horror set during a night shift in an old hospital. Follow medical orders, spot anomalies, and survive until dawn!

### About the game

> You are the night orderly in an old hospital. Check the duty log and patient wristbands, carry out medical orders, and keep the ward running until 06:00. The game contains 11 night shifts, including a blackout, quarantine, transfusion, missing patient, fire, surgery, and other stories. Familiar corridors slowly change while dangerous anomalies appear among patients and staff. Explore in first person, use your torch, notice what does not belong, and protect your health and mind. Progress is saved between sessions. The game supports English and Russian, keyboard and mouse, and touch controls.

### Short description

> Survive eleven night shifts in a hospital that never sleeps.

### How to play

> Choose a shift and start your duty. Read the log and assignment board, answer calls, find the required items, check patient wristbands, and complete the mandatory tasks before 06:00. Avoid dangerous anomalies and watch your health and mind. On desktop, use WASD to move, the mouse to look, E to act, F for the torch, and Esc to pause. On mobile, use the left stick to move, swipe on the right to look, and use the Action, Torch, and pause buttons.

## 5. Файлы для загрузки

Общие для обеих локализаций:

- Иконка: `build/yandex_media/card/icon_512x512.png`
- Maskable-иконка, если заполняем необязательное поле: тот же `icon_512x512.png`
- Обложка: `build/yandex_media/card/cover_800x470.png`

Русская локализация:

- Десктопные скриншоты: `build/yandex_media/screenshots/ru/01`–`04`
- Мобильные скриншоты: `build/yandex_media/screenshots/mobile/ru/01`–`04`
- Горизонтальное видео: `build/yandex_media/video/Palata_0_gameplay_RU.mp4`

Английская локализация:

- Десктопные скриншоты: `build/yandex_media/screenshots/en/01`–`04`
- Мобильные скриншоты: `build/yandex_media/screenshots/mobile/en/01`–`04`
- Горизонтальное видео: `build/yandex_media/video/Palata_0_gameplay_EN.mp4`

Кадры `00_menu_*` оставлены как дополнительные; для обязательных скриншотов лучше использовать реальный игровой процесс `01`–`04`.

## 6. Перед отправкой на модерацию

1. Открыть загруженный архив через `Открыть черновик с debug-панелью`.
2. Проверить русский и английский через SDK mocks.
3. Проверить на десктопе и реальном Android-устройстве: старт, паузу при потере фокуса, рекламу и возврат из неё, звук, повторный запуск и облачное сохранение.
4. Если добавляется iOS, указать Apple Team ID и отдельно проверить на реальном iPhone/iPad.
5. После успешной проверки отправить черновик на модерацию.

Актуальная инструкция: <https://yandex.ru/dev/games/doc/ru/console/add-new-game/draft>

