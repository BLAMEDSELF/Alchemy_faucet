# Sepolia Faucet Automation

## Description (ENG)
This Python script automates the process of requesting Sepolia testnet ETH tokens from the Alchemy faucet (`https://www.alchemy.com/faucets/ethereum-sepolia`). It leverages Selenium for browser automation, CapSolver for solving reCAPTCHA challenges, and supports proxy usage to manage multiple requests. The script is designed for educational purposes, showcasing web scraping, automation techniques, and CLI interactivity.

### Features
- Randomized User-Agent generation to mimic human behavior.
- Proxy support with authentication via dynamically generated Chrome extensions.
- Automatic reCAPTCHA solving using the CapSolver API.
- Interactive command-line interface (CLI) menu powered by `questionary`.
- Robust error handling with retries for failed attempts.
- Colorful console output using `colorama`.

---

## Описание (RU)
Этот Python-скрипт автоматизирует процесс запроса тестовых токенов Sepolia ETH из faucet Alchemy (`https://www.alchemy.com/faucets/ethereum-sepolia`). Он использует Selenium для автоматизации браузера, CapSolver для решения задач reCAPTCHA и поддерживает прокси для обработки нескольких запросов. Скрипт создан в образовательных целях и демонстрирует техники веб-скрапинга, автоматизации и взаимодействия через CLI.

### Особенности
- Генерация случайного User-Agent для имитации человеческого поведения.
- Поддержка прокси с аутентификацией через динамически создаваемые расширения Chrome.
- Автоматическое решение reCAPTCHA с помощью API CapSolver.
- Интерактивное меню в командной строке на базе `questionary`.
- Надёжная обработка ошибок с повторными попытками.
- Цветной вывод в консоль с использованием `colorama`.

## Установка и запуск
### Установите зависимости:
pip install -r requirements.txt
### Запуск (первый модуль, потом второй):
 python main.py
---

## Project Structure
