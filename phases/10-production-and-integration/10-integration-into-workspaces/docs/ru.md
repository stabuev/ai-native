# Урок 10.1 · Интеграция в рабочие пакеты

**Фаза 10 — Production и интеграция** · **Результат фазы:** Встроить ИИ в рабочий инструмент с мониторингом токенов и стоимости.
<!-- **Requires:** лицензия Copilot/Gemini или API-ключ — только для блока USE IT -->

> **MOTTO.** ИИ полезен, когда встроен в работу: фича-флаг + fallback делают встраивание безопасным.

## PROBLEM

Демо в чате ≠ прод. Встраивая ИИ в реальный процесс (CRM, поддержка, документы), нельзя допустить, чтобы сбой модели или плохой ответ положил рабочий инструмент. Нужны **фича-флаг** (мгновенно выключить) и **graceful fallback** (упала модель → процесс деградирует, а не падает). ИИ должен быть заменяемой деталью.

## CONCEPT

```
существующий процесс
   └─ [ AI-шаг ]
        enabled? ──нет──► fallback (старый детерминированный путь)
        try AI ──ошибка──► fallback
        ok ──► AI-результат
```

Точки встраивания ищем там, где ИИ даёт ценность (черновик, классификация, саммари), но всегда с запасным путём. Это делает откат безрисковым.

## BUILD IT

Безопасная обёртка ИИ-шага: [`code/integration.py`](../code/integration.py).

- `AIFeature(fn, fallback, enabled)` — фича-флаг + try/except → fallback;
- `run_pipeline(steps, x)` — ИИ как один из шагов существующего пайплайна.

```bash
python code/integration.py
pytest code -q
```

Демо показывает три исхода: ИИ работает; ИИ упал → fallback; фича выключена → fallback. Прод не падает из-за ИИ — ключевое свойство интеграции.

## USE IT

Встраивание через рабочие пакеты (мульти-провайдер):

- **Microsoft 365 Copilot** — ИИ в Word/Excel/Outlook/Teams поверх Microsoft Graph (доступ только к тому, что разрешено пользователю).
- **Gemini for Google Workspace** — ИИ в Gmail/Docs/Sheets; данные не покидают организацию.
- **Свой инструмент через API** — AI-шаг за фича-флагом и fallback (как в Build It), с мониторингом (10.2).

Везде принцип один: ИИ рядом с данными процесса + контроль доступа и откат.

## SHIP IT

**Артефакт:** План интеграции для команды → [`outputs/integration-plan.md`](../outputs/integration-plan.md)

Шаблон: где встроить ИИ, какой fallback, как включать (rollout/флаги), что мониторить. Дальше: деплой и мониторинг (10.2), телеметрия (10.3).

## Материалы

- [Microsoft 365 Copilot — Overview](https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-overview) — ИИ в рабочих приложениях.
- [Gemini for Google Workspace](https://support.google.com/docs/answer/13952129) — ИИ в Gmail/Docs/Sheets.
- [Microsoft 365 Copilot — архитектура](https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-architecture) — данные, доступ, границы безопасности.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
