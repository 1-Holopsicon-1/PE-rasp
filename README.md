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

Фронт собирается вручную (Nix не собирает Node-зависимости — нет хешей,
нет офлайн-кеша). Nix только раздаёт статику и предоставляет парсер.

```bash
# 1. Собрать фронт локально или на сервере:
yarn install && yarn build    # результат в build/

# 2. Обновить расписание: положить PDF в pdf/, затем
raspisanie-parse              # парсер доступен через NixOS-модуль

# 3. Раздавать (вручную):
python3 -m http.server 8080 --directory build
```

### NixOS-модуль

Модуль поднимает systemd-сервис `raspisanie.service` — раздаёт `build/`
через `python3 -m http.server`. Статика должна лежать в `dataDir`
(по умолчанию `/opt/PE-rasp/build`).

В `configuration.nix`:

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
          services.raspisanie.dataDir = "/opt/PE-rasp/build";
        }
      ];
    };
  };
}
```

`nixos-rebuild switch` — сервис поднимется. `raspisanie-parse` попадёт в
PATH. Для обновления расписания: положить PDF в `pdf/`, запустить
`raspisanie-parse`, перезапустить сервис `systemctl restart raspisanie`.

## Фильтры

- Вид спорта (множественный выбор чипами)
- Локация (СК / Спортзал)
- Метро
- Поиск по тексту
- Навигация по дням (Пн–Сб)
- Подсветка сегодняшнего дня и идущего слота
- Карточка "ближайшая пара" сверху