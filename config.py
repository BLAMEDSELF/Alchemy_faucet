# config.py

# Ваш API-ключ от CapSolver
CAPSOLVER_API_KEY = "CAP-..."

# Список словарей с адресами кошельков и прокси (если прокси не нужен, оставьте пустую строку "")
accounts = [
    {
        "wallet": "0xYourWallet",
        "proxy": "http://user:Password@IP:PORT"  # Пример формата прокси
    },
    {
        "wallet": "0xYourWallet",
        "proxy": ""  # Без прокси
    }
    # Добавьте столько аккаунтов, сколько нужно
]