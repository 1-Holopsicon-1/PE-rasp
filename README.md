# Расписание элективных дисциплин

Личный инструмент для просмотра расписания элективных дисциплин по физкультуре
и спорту. Python-парсер читает PDF из `pdf/` через pdfplumber и складывает JSON
в `static/data/`, SvelteKit-приложение рендерит расписание с фильтрами, тёмной
темой и mobile-first адаптивом.

## Технологии

- SvelteKit + TypeScript + TailwindCSS
- @sveltejs/adapter-static
- Python 3 + pdfplumber (через `uv tool run`)

## Разработка

```sh
npm install
npm run dev
```

## Сборка

```sh
npm run build
```