import os
import shutil
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from colorama import init, Fore, Style
from config import accounts, CAPSOLVER_API_KEY
import questionary
from questionary import Choice

# Инициализация colorama для цветного вывода
init()

# Генерация случайного User-Agent
def generate_user_agent():
    base_ua = "Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    platforms = ["Windows NT 10.0; Win64; x64", "Macintosh; Intel Mac OS X 10_15_7", "X11; Linux x86_64"]
    suffix = random.choice(["", " Edg/134.0.0.0", " OPR/120.0.0.0"])
    return base_ua.format(platform=random.choice(platforms)) + suffix

# Проверка прокси с повторными попытками
def check_proxy(proxy, max_retries=3, backoff_factor=2):
    if not proxy:
        print(f"{Fore.YELLOW}Прокси не указан{Style.RESET_ALL}")
        return True
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))
            proxies = {"http": proxy, "https": proxy}
            start_time = time.time()
            response = session.get("https://www.google.com", proxies=proxies, timeout=10)
            response_time = time.time() - start_time
            ip = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10).json()["ip"]
            print(f"{Fore.GREEN}IP прокси: {ip} ({response_time:.2f} сек){Style.RESET_ALL}")
            return True if response.status_code == 200 else False
        except Exception as e:
            print(f"{Fore.RED}Ошибка прокси: {e} (попытка {attempt + 1}/{max_retries}){Style.RESET_ALL}")
            if attempt < max_retries - 1:
                delay = backoff_factor * (2 ** attempt)
                print(f"{Fore.YELLOW}Ждем {delay} сек...{Style.RESET_ALL}")
                time.sleep(delay)
    print(f"{Fore.RED}Прокси не работает{Style.RESET_ALL}")
    return False

# Разбор строки прокси
def parse_proxy(proxy):
    if not proxy:
        return None, None, None, None
    proxy = proxy.replace("http://", "")
    auth, host_port = proxy.split("@")
    username, password = auth.split(":")
    host, port = host_port.split(":")
    return host, port, username, password

# Создание расширения для прокси
def create_proxy_extension(proxy, index):
    temp_dir = os.path.join(tempfile.gettempdir(), f"proxy_extension_{index}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    manifest = '{"version": "1.0.0", "manifest_version": 2, "name": "Proxy Auth Extension", "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"], "background": {"scripts": ["background.js"]}, "minimum_chrome_version": "22.0.0"}'
    with open(os.path.join(temp_dir, "manifest.json"), "w") as f:
        f.write(manifest)

    host, port, username, password = parse_proxy(proxy)
    background_script = f'var config = {{mode: "fixed_servers", rules: {{singleProxy: {{scheme: "http", host: "{host}", port: parseInt("{port}")}}, bypassList: ["localhost"]}}}}; chrome.proxy.settings.set({{value: config, scope: "regular"}}, function(){{}}); function callbackFn(details) {{return {{authCredentials: {{username: "{username}", password: "{password}"}}}}}} chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ["blocking"]);'
    with open(os.path.join(temp_dir, "background.js"), "w") as f:
        f.write(background_script)

    return temp_dir

# Решение reCAPTCHA через CapSolver
def solve_recaptcha(proxy, website_key, timeout=120):
    url = "https://api.capsolver.com/createTask"
    data = {"clientKey": CAPSOLVER_API_KEY, "task": {"type": "ReCaptchaV2Task", "websiteURL": "https://www.alchemy.com/faucets/ethereum-sepolia", "websiteKey": website_key}}
    balance = requests.post("https://api.capsolver.com/getBalance", json={"clientKey": CAPSOLVER_API_KEY}, timeout=10).json().get("balance", 0)
    print(f"{Fore.MAGENTA}Баланс CapSolver: ${balance}{Style.RESET_ALL}")
    if balance <= 0:
        raise Exception("Недостаточно средств на CapSolver")

    response = requests.post(url, json=data, timeout=10).json()
    task_id = response.get("taskId")
    if not task_id:
        raise Exception(f"Не удалось создать задачу: {response}")

    print(f"{Fore.YELLOW}Решаем reCAPTCHA...{Style.RESET_ALL}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        status_response = requests.post("https://api.capsolver.com/getTaskResult", json={"clientKey": CAPSOLVER_API_KEY, "taskId": task_id}, timeout=10).json()
        status = status_response.get("status")
        if status == "ready":
            print(f"{Fore.GREEN}reCAPTCHA решена{Style.RESET_ALL}")
            return status_response["solution"]["gRecaptchaResponse"]
        elif status == "failed":
            raise Exception(f"CapSolver ошибка: {status_response.get('errorDescription', 'Неизвестно')}")
        time.sleep(2)
    raise Exception(f"Таймаут reCAPTCHA ({timeout} сек)")

# Получение токенов Sepolia
def get_sepolia_tokens(wallet, proxy, index, max_attempts=3):
    ua = generate_user_agent()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={ua}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    temp_dir = None
    if proxy and check_proxy(proxy):
        temp_dir = create_proxy_extension(proxy, index)
        options.add_argument(f'--load-extension={temp_dir}')
    else:
        print(f"{Fore.YELLOW}Работаем без прокси{Style.RESET_ALL}")

    driver = None
    log_output = "nul" if os.name == "nt" else "/dev/null"
    service = Service(ChromeDriverManager().install(), log_output=log_output)
    service.silent = True

    for attempt in range(max_attempts):
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined}); window.navigator.chrome = { runtime: {} }; Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]}); Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"})
            
            driver.get("https://api.ipify.org?format=json")
            driver.get("https://www.alchemy.com/faucets/ethereum-sepolia")
            time.sleep(20)

            wait = WebDriverWait(driver, 30)
            input_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@class, 'alchemy-faucet-panel-input-text')]")))
            input_field.clear()
            input_field.send_keys(wallet)

            actions = ActionChains(driver)
            actions.move_to_element(input_field).click().pause(random.uniform(1, 3)).perform()
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'alchemy-faucet-button')]")))
            actions.move_to_element(submit_button).pause(random.uniform(1, 2)).click().perform()

            try:
                alert = Alert(driver)
                alert.accept()
                time.sleep(5)
            except:
                pass

            recaptcha_iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha')]")))
            from urllib.parse import urlparse, parse_qs
            iframe_src = recaptcha_iframe.get_attribute("src")
            website_key = parse_qs(urlparse(iframe_src).query).get("k", [None])[0]
            if not website_key:
                raise Exception("data-sitekey не найден")

            response = solve_recaptcha(proxy, website_key)
            driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML='{response}';")
            submit_button.click()
            print(f"{Fore.GREEN}Запрос отправлен{Style.RESET_ALL}")

            time.sleep(5)
            try:
                success_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'Success') or contains(text(), 'confirmed')]").text
                print(f"{Fore.GREEN}Ответ faucet: {success_msg}{Style.RESET_ALL}")
            except:
                print(f"{Fore.YELLOW}Подтверждение не найдено{Style.RESET_ALL}")
            break

        except Exception as e:
            print(f"{Fore.RED}Попытка {attempt + 1}/{max_attempts} не удалась: {e}{Style.RESET_ALL}")
            if attempt == max_attempts - 1:
                print(f"{Fore.RED}Все попытки исчерпаны для {wallet}{Style.RESET_ALL}")
            else:
                time.sleep(random.uniform(5, 10))
        finally:
            if driver:
                driver.quit()

    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

# Функция для выбора модуля
def get_module():
    result = questionary.select(
        "Choose module",
        choices=[
            Choice("1) Start faucet", 1),
            Choice("2) Exit", 2),
        ],
        qmark="⚙️",
        pointer="✅"
    ).ask()
    return result if result is not None else 2  # Выход при отмене

# Основная функция
def main():
    choice = get_module()
    if choice == 1:
        print(f"{Fore.GREEN}Запуск модуля faucet...{Style.RESET_ALL}")
        for index, account in enumerate(accounts):
            wallet = account["wallet"]
            proxy = account.get("proxy", None)
            print(f"{Fore.BLUE}--- Аккаунт {index}: {wallet} ---{Style.RESET_ALL}")
            get_sepolia_tokens(wallet, proxy, index)
            time.sleep(random.uniform(10, 20))
    elif choice == 2:
        print(f"{Fore.YELLOW}Выход...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()