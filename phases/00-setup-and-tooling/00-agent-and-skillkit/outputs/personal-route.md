# Артефакт: персональный маршрут по курсу

Результат прохождения `/find-your-level` — твой план обучения. Ниже **пример** для профиля «Практик» (балл 11). Свой маршрут получи через скилл или движок [`code/find_your_level.py`](../code/find_your_level.py).

## Пример: Практик · балл 11 · ~190 ч

| Фаза | Название | Действие | Часы |
|---|---|---|---|
| 0 | Setup & Tooling | skim | 4 |
| 1 | Как работают LLM | skim | 6 |
| 2 | Промпт-инжиниринг | focus | 16 |
| 3 | Текст и документы | focus | 14 |
| 4 | Скиллы, память, проекты | focus | 16 |
| 5 | Данные и аналитика | focus | 18 |
| 6 | Инструменты и MCP | focus | 18 |
| 7 | Agent Engineering | focus | 18 |
| 8 | Мульти-агенты | focus | 14 |
| 9 | FinOps | focus | 14 |
| 10 | Production | focus | 12 |
| 11 | Этика и governance | focus | 10 |
| 12 | Capstone | focus | 30 |

**Действия:** `focus` — проходить подробно; `skim` — пролистать (≈половина часов); `skip` — пропустить.

## Как сгенерировать свой

```bash
# из code/ урока 0.3 или из .claude/skills/find-your-level/
python -c "import find_your_level as f, json; \
print(json.dumps(f.route(f.score([2,2,1,1,1,1,1,0,1,1])), ensure_ascii=False, indent=2))"
```

Замени список индексов на свои ответы (по одному `0..3` на каждый из 10 вопросов). После ключевых фаз прогоняй `/check-understanding <phase>`, чтобы свериться.
