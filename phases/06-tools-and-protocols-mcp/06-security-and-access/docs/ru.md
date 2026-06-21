# Урок 6.5 · Безопасность и доступ

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.

> **MOTTO.** Между моделью и действием всегда стоит авторизация: модель просит — сервер решает, можно ли.

## PROBLEM

MCP-сервер даёт модели руки: файлы, БД, отправка писем. Если сервер слепо исполняет всё, что просит модель, одна prompt-инъекция — и `delete_file('/')` или утечка секретов. Нужен **слой доступа**: кто (principal) что (tool) над чем (args) может, плюс изоляция и аудит.

## CONCEPT

```
модель → tool_call → [ авторизация ] → исполнение
                         │ principal: какие инструменты разрешены
                         │ право на запись (read-only по умолчанию)
                         │ валидация аргументов (path traversal, scope)
                         ▼ deny + audit, если нельзя
```

Принципы: **least privilege** (минимум прав), **read-only по умолчанию**, **валидация входов**, **аудит**. MCP в проде использует OAuth 2.1 для HTTP-транспорта; для STDIO — секреты из окружения.

## BUILD IT

Слой контроля доступа, без зависимостей: [`code/mcp_security.py`](../code/mcp_security.py).

- `Principal(name, allowed_tools, can_write)` — кто и что может;
- `check_access(principal, tool, args)` — разрешить/запретить + причина;
- `is_safe_path(path)` — защита от path traversal;
- `guarded_call(...)` — проверка + вызов + запись в аудит.

```bash
python code/mcp_security.py
pytest code -q
```

Тесты ловят реальные угрозы: вызов неразрешённого инструмента, запись без прав, `../../etc/passwd`.

## USE IT

Что нельзя отдавать модели — практика (мульти-платформа):

- **Не давай write/delete по умолчанию** — read-only, запись только явным principal'ам.
- **Не клади секреты в ответы инструментов** и в схемы — модель их «запомнит» и может разгласить.
- **Минимизируй scope токенов** — не `db:*`/`admin:*`, а точечные права (Rich Authorization Requests).
- **HTTP-транспорт → OAuth 2.1**: сервер как Resource Server, проверка audience токена; STDIO → секреты из env.
- **Санитизируй входы** и опасайся «confused deputy» у прокси-серверов.

⚠️ Связка с prompt-инъекциями (Фаза 11): данные из инструментов могут содержать вредоносные инструкции.

## SHIP IT

**Артефакт:** Чек-лист безопасности MCP → [`outputs/mcp-security-checklist.md`](../outputs/mcp-security-checklist.md)

Чек-лист перед выкладкой сервера: права, изоляция, секреты, токены, валидация, аудит. Завершает Фазу 6 — сервер с контролем доступа.

## Материалы

- [MCP — Security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices) — риски и меры (в т.ч. confused deputy).
- [MCP — Authorization (spec)](https://modelcontextprotocol.io/specification/2025-11-25) — OAuth 2.1, Resource Indicators.
- [Red Hat — MCP security risks and controls](https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls) — практический разбор рисков.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
