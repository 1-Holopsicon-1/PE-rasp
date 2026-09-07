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
npm install
# Python для парсера через uv (ставится отдельно):
# curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Использование

1. Положить PDF в `pdf/`.
2. Запустить парсер:
   ```bash
   npm run parse
   # или явно:
   uv tool run --from pdfplumber python3 scripts/parse.py pdf/file.pdf
   ```
3. Запустить dev-сервер:
   ```bash
   npm run dev
   ```
4. Открыть http://localhost:5173

## Сборка статики

```bash
npm run build
# результат в build/
```

## Деплой через Nix

На NixOS-сервере:

```bash
# собрать
nix build .#default
# результат в ./result — директория со статикой + bin/raspisanie-parse

# обновить расписание: положить PDF в pdf/, затем
./result/bin/raspisanie-parse

# раздавать (через nginx или python http.server)
python3 -m http.server 8080 --directory result
```

### NixOS-модуль

В `configuration.nix`:

```nix
{
  inputs.raspisanie.url = "github:you/PHe-rsap";  # или путь
  outputs = { self, nixpkgs, raspisanie, ... }: {
    nixosConfigurations.server = nixpkgs.lib.nixosSystem {
      modules = [
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

После деплоя: `raspisanie-parse` из PATH сервера для обновления JSON.

## Фильтры

- Вид спорта (множественный выбор чипами)
- Локация (СК / Спортзал)
- Метро
- Поиск по тексту
- Навигация по дням (Пн–Сб)
- Подсветка сегодняшнего дня и идущего слота
- Карточка "ближайшая пара" сверху