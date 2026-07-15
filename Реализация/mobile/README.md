# Belarusbank Investments

Адаптивный демонстрационный клиент брокерского приложения на Flet 0.86.0.
При недоступном Django API интерфейс автоматически использует демо-данные и
показывает индикатор «Демо-данные».

Для локальных команд `flet run` установите CLI и обе среды Flet 0.86 один раз
(минимальная установка `flet` не включает их):

```powershell
cd C:\Users\user\Desktop\bank\Реализация\mobile
..\.venv\Scripts\python.exe -m pip install "flet[all]==0.86.0"
```

## Запуск в браузере

Из PowerShell:

```powershell
cd C:\Users\user\Desktop\bank\Реализация\mobile
$env:BROKER_API_URL = "http://127.0.0.1:8000/api"
..\.venv\Scripts\flet.exe run --web src\main.py
```

Без переменной `BROKER_API_URL` используется адрес
`http://127.0.0.1:8000/api`.

## Запуск как desktop-приложение

```powershell
cd C:\Users\user\Desktop\bank\Реализация\mobile
..\.venv\Scripts\flet.exe run src\main.py
```

## Web-сборка

```powershell
cd C:\Users\user\Desktop\bank\Реализация\mobile
..\.venv\Scripts\flet.exe build web
```

Результат будет создан в `build\web`.

## Android APK

Установите требования Flet для Android (Flutter SDK, Android SDK и Java), затем:

```powershell
cd C:\Users\user\Desktop\bank\Реализация\mobile
..\.venv\Scripts\flet.exe build apk
```

Результат будет создан в `build\apk`. APK-сборка может при первом запуске
загрузить Android/Flutter-зависимости.

## Тесты и проверки

```powershell
cd C:\Users\user\Desktop\bank\Реализация\mobile
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\.venv\Scripts\python.exe -m compileall -q src tests
```

Демо-вход принимает любые непустые логин и пароль. Финансовые операции в
офлайн-режиме намеренно не имитируются как успешные: API должен подтвердить
пополнение, вывод и торговую заявку.
