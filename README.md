# Расписание элективных дисциплин — веб-вьюер

Личный инструмент: парсит PDF-расписание физкультуры через pdfplumber и
рендерит SvelteKit-приложение с тёмной темой и фильтрами.

## Структура

- `pdf/` — входные PDF (положи сюда новый файл расписания)
- `scripts/parse.py` — парсер PDF → JSON
- `static/data/raspisanie.json` — данные, читаемые фронтом
- `src/` — SvelteKit-приложение

## Установка

```bash
yarn install
# Python для парсера через uv (ставится отдельно):
# curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Использование

1. Положить PDF в `pdf/`.
2. Запустить парсер:
   ```bash
   yarn parse
   # или явно:
   uv tool run --from pdfplumber python3 scripts/parse.py pdf/file.pdf
   ```
3. Запустить dev-сервер:
   ```bash
   yarn dev
   ```
4. Открыть http://localhost:5173

## Сборка статики

```bash
yarn build
# результат в build/
```

## Деплой через Nix

Nix собирает фронт через `yarn-berry_4` (офлайн-кеш зависимостей) и
упаковывает парсер. Один `nixos-rebuild switch` — и сервис работает.

### Первый прогон: получить хеш офлайн-кеша

В `flake.nix` поле `hash = ""` — первая сборка упадёт с сообщением:

```
specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
got:       sha256-<реальный_хеш>=
```

Скопировать `got:` → вставить в `hash` в `flake.nix`, закоммитить, пересобрать.

### NixOS-модуль

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    raspisanie.url = "path:/opt/PE-rasp";
  };

  outputs = { self, nixpkgs, raspisanie, ... }: {
    nixosConfigurations.server = nixpkgs.lib.nixosSystem {
      modules = [
        ./hardware-configuration.nix
        raspisanie.nixosModules.default
        {
          services.raspisanie.enable = true;
          services.raspisanie.port = 8080;
        }
      ];
    };
  };
}
```

`nixos-rebuild switch` — сервис поднимется, `raspisanie-parse` попадёт в PATH.

### Обновление расписания

```bash
# положить PDF в pdf/, затем:
raspisanie-parse                  # перегенерить JSON
nixos-rebuild switch              # пересобрать (подхватит новый JSON)
```
## Фильтры

- Вид спорта (множественный выбор чипами)
- Локация (СК / Спортзал)
- Метро
- Поиск по тексту
- Навигация по дням (Пн–Сб)
- Подсветка сегодняшнего дня и идущего слота
- Карточка "ближайшая пара" сверху