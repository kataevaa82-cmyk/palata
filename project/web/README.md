# `project/web/` — HTML-оболочка для Яндекс Игр

Здесь лежит `yandex_shell.html` — исходник, а не артефакт сборки. Godot
подставляет его как `html/custom_html_shell` (`export_presets.cfg:73`) и
сворачивает в `build/yandex/index.html` при экспорте.

Каталог до 18 сентября 2026 года был исключён `.gitignore`, поэтому файла в
репозитории нет. Это ошибка: в оболочке живёт весь мост к SDK, её
собственная локализация и единственная в проекте обработка портретной
ориентации. Без неё веб-экспорт указывает на несуществующий файл, а
`validate_yandex_integration.gd` падает на `shell_missing`.

## Как вернуть оригинал

Оболочка существует и проверена: `YANDEX_RELEASE_CHECKLIST.md` фиксирует
успешный экспорт и архив с записанным SHA-256. Порядок поиска:

1. Рабочая копия на машине автора: `C:\palata\project\web\yandex_shell.html`.
   Это предпочтительный источник — именно он собирал `1.0.0`.
2. `build/yandex/index.html` — оболочка уже с подставленными значениями.
   Godot заменяет в ней `$GODOT_URL`, `$GODOT_PROJECT_NAME`,
   `$GODOT_HEAD_INCLUDE`, `$GODOT_CONFIG`, `$GODOT_SPLASH_COLOR`,
   `$GODOT_SPLASH` и `$GODOT_THREADS_ENABLED`; чтобы получить шаблон, эти
   места надо вернуть обратно в плейсхолдеры.
3. `build/Palata_0_Yandex.zip`, корневой `index.html` — то же самое.

Положить файл сюда и закоммитить. `git add -f` больше не нужен: каталог
разблокирован.

## Контракт

Если оригинал утрачен целиком, оболочку придётся написать заново. Ниже —
всё, что от неё требует код и проверки.

### Интерфейс для Godot

`yandex_sdk.gd:80` берёт `JavaScriptBridge.get_interface("YandexGamesBridge")`,
то есть оболочка обязана определить глобальный объект `YandexGamesBridge` с
методами:

| Метод | Что делает |
|---|---|
| `connectGodot(callback)` | Запоминает колбэк Godot. Колбэк вызывается как `callback(имя_события, payload)`; события, случившиеся до подключения, надо буферизовать и отдать сразу после. |
| `loadingReady()` | `ysdk.features.LoadingAPI?.ready()` |
| `setGameplayActive(value)` | `GameplayAPI?.start()` / `GameplayAPI?.stop()` |
| `showInterstitial()` | `ysdk.adv.showFullscreenAdv({ callbacks: ... })` |
| `saveData(json, flushCloud)` | `player.setData({ palata0: JSON.parse(json) }, flushCloud)` |

Ключ сохранения — `palata0` (`yandex_sdk.gd`, `SAVE_KEY`).

### События в Godot

`_on_bridge_event()` разбирает эти имена, остальные игнорируются:

| Событие | Payload | Когда |
|---|---|---|
| `sdk_ready` | JSON `{"language": "ru", "device_type": "mobile"}` | `YaGames.init()` выполнен |
| `sdk_unavailable` | — | инициализация не удалась или вышло время |
| `cloud_data` | JSON сохранения (содержимое ключа `palata0`) | `player.getData(['palata0'])` вернулся |
| `platform_pause` | — | `ysdk.on('game_api_pause')` |
| `platform_resume` | — | `ysdk.on('game_api_resume')`, закрытие рекламы |
| `ad_open` | — | реклама открылась |
| `ad_close` | — | реклама закрылась (обязательно, иначе игра ждёт колбэк) |

`device_type` должен быть одним из `desktop`, `mobile`, `tablet`, `tv` —
остальные значения `_apply_environment_payload()` отбрасывает.

### Обязательные строки

`validate_yandex_integration.gd:239–244` ищет их в исходнике оболочки:

```
src="/sdk.js"        YaGames.init()       LoadingAPI?.ready()
GameplayAPI?.start()  game_api_pause       showFullscreenAdv
player.getData        player.setData       contextmenu
orientation: portrait mobile-device        rotate-notice
```

`tools/build/pack_yandex_zip.py:39–41` ищет в уже собранном `index.html`
тот же список без `game_api_pause`, `contextmenu` и `orientation: portrait`,
но дополнительно `SHELL_TEXT` и `data-i18n`.

Это не формальность: если экспорт молча откатится на стандартную оболочку
Godot, пропадут все хуки SDK разом, и проверка по строкам — единственное,
что это ловит.

### Поведение

По `YANDEX_RELEASE_CHECKLIST.md`:

- SDK подключается только относительным путём `/sdk.js`; сам файл в архив
  не кладётся — Яндекс раздаёт его сам;
- `SHELL_TEXT` — словарь строк оболочки; элементы с `data-i18n`
  и `<title>` переводятся по `navigator.language`;
- `rotate-notice` — полноэкранная просьба повернуть устройство, показывается
  через `@media (orientation: portrait)` и только при классе `mobile-device`
  на `<body>`;
- контекстное меню, выделение и перетаскивание страницы подавлены;
- canvas занимает всё окно без растяжения изображения
  (`html/canvas_resize_policy=2`);
- экспорт однопоточный, без COOP/COEP.
