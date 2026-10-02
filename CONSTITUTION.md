# kvant — Constitution

> The non-negotiable rules. Every RFC, spec and pull request is checked against this. If a
> change conflicts with it, stop and say so — amend it deliberately instead of working around it.
> Keep it short: a rule that cannot be checked is a wish.

**Version:** 1.0.0 · **Ratified:** 2026-10-01

## Principles
1. Спецификация до кода — ничего не реализуется без одобренной владельцем спецификации.
2. Быстрый ввод прежде всего — записать трату можно без открытия Telegram.
3. Рубль — основная валюта: каждая запись хранит исходную сумму, валюту и курс дня, итоги считаются в рублях.
4. Изменения передаются владельцу полными файлами (архив и готовая команда для терминала), а не фрагментами.

## Guardrails (things that must never happen)
- Токены, пароли и ключи никогда не попадают в репозиторий — только в переменные окружения.
- Нельзя пересчитывать старые записи по сегодняшнему курсу.
- Анимации не работают при включённой в системе настройке «Уменьшение движения».

## Quality gates (what "done" means)
- Тесты проходят (`uv run pytest`), критерии приёмки из спецификации покрыты тестами.
- В спецификации описано, как владельцу проверить функцию руками.

## Amendments
_None yet._
