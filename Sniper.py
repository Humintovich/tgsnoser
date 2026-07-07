#!/usr/bin/env python3
import subprocess, sys, importlib, os, time, random, string, json, threading, requests

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_install():
    required = ['requests']
    for pkg in required:
        try:
            importlib.import_module(pkg.replace('-', '_'))
        except ImportError:
            print(f"[+] Устанавливаю модуль: {pkg}...")
            install_package(pkg)

check_and_install()

BOT_TOKEN = "8317237541:AAGKsD0pi_3hHah9ihjSpYiZPYJysRvwIRo"
YOUR_ACCOUNT_ID = "8597812279"
CONFIG_FILE = os.path.expanduser("~/.sniper_config.json")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"length": 5, "with_digits": True, "with_underscore": True, "prefix": "", "suffix": "", "max_results": 10}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except:
        pass

def check_username_fragment(username):
    try:
        url = f"https://fragment.com/api/v1/username/{username}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'application/json'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('available', False):
                return True
            else:
                return False
        elif r.status_code == 404:
            return True
        else:
            return None
    except:
        return None

def generate_usernames(config):
    length = config.get("length", 5)
    with_digits = config.get("with_digits", True)
    with_underscore = config.get("with_underscore", True)
    prefix = config.get("prefix", "")
    suffix = config.get("suffix", "")
    count = config.get("max_results", 10) * 5
    chars = string.ascii_lowercase
    if with_digits:
        chars += string.digits
    if with_underscore:
        chars += '_'
    usernames = set()
    attempts = 0
    while len(usernames) < count and attempts < 10000:
        attempts += 1
        middle_len = length - len(prefix) - len(suffix)
        if middle_len < 1:
            middle_len = length
            prefix = ""
            suffix = ""
        middle = ''.join(random.choices(chars, k=middle_len))
        username = prefix + middle + suffix
        if len(username) < 5:
            continue
        if not username[0].isalpha():
            continue
        if username.startswith('_') or username.endswith('_'):
            continue
        if '__' in username:
            continue
        usernames.add(username)
    return list(usernames)

def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': YOUR_ACCOUNT_ID, 'text': text, 'parse_mode': 'HTML'}
        requests.post(url, data=data, timeout=5)
    except:
        pass

def run_sniper(config, stop_event):
    print(f"[*] Начинаем поиск...")
    print(f"[*] Длина: {config.get('length', 5)}")
    print(f"[*] Цифры: {'Да' if config.get('with_digits', True) else 'Нет'}")
    print(f"[*] Подчёркивания: {'Да' if config.get('with_underscore', True) else 'Нет'}")
    print(f"[*] Префикс: {config.get('prefix', '') or 'нет'}")
    print(f"[*] Суффикс: {config.get('suffix', '') or 'нет'}")
    print(f"[*] Ищем до {config.get('max_results', 10)} юзернеймов\n")
    print("[*] Проверка через Fragment.com\n")
    found = []
    checked = 0
    while len(found) < config.get('max_results', 10) and not stop_event.is_set():
        usernames = generate_usernames(config)
        for username in usernames:
            if stop_event.is_set():
                break
            checked += 1
            if checked % 10 == 0:
                print(f"[*] Проверено: {checked}, найдено: {len(found)}")
            status = check_username_fragment(username)
            if status is True:
                print(f"[+] ✅ {username} – Свободен!")
                found.append(username)
                send_telegram_message(f"🎯 Найден свободный юзернейм!\n@{username}\n\nЗайми скорее!")
                if len(found) >= config.get('max_results', 10):
                    break
            elif status is False:
                print(f"[-] ❌ @{username} – Занят")
            else:
                print(f"[?] ⚠️ @{username} – Ошибка")
            time.sleep(0.3)
        time.sleep(1)
    if found:
        print(f"\n[+] Найдено свободных юзернеймов: {len(found)}")
        for u in found:
            print(f"  - @{u}")
        send_telegram_message(f"📋 ИТОГОВЫЙ СПИСОК:\n\n" + "\n".join([f"@{u}" for u in found]))
    else:
        print("\n[-] Свободных юзернеймов не найдено.")
        send_telegram_message("❌ Свободных юзернеймов не найдено.")
    print("\n[*] Снипер завершил работу.")

def menu():
    config = load_config()
    stop_event = threading.Event()
    sniper_thread = None
    while True:
        clear_screen()
        print("""
╔═══════════════════════════════════════╗
║   TELEGRAM USERNAME SNIPER v3.0      ║
║   (БЕЗ API, только Fragment)         ║
╚═══════════════════════════════════════╝
        """)
        print(f"  Текущие настройки:")
        print(f"  ─────────────────────────")
        print(f"  Длина юзернейма: {config.get('length', 5)}")
        print(f"  Цифры: {'Да' if config.get('with_digits', True) else 'Нет'}")
        print(f"  Подчёркивания: {'Да' if config.get('with_underscore', True) else 'Нет'}")
        print(f"  Префикс: {config.get('prefix', '') or 'нет'}")
        print(f"  Суффикс: {config.get('suffix', '') or 'нет'}")
        print(f"  Макс. результатов: {config.get('max_results', 10)}")
        print()
        print("  1. Запустить поиск")
        print("  2. Остановить поиск")
        print("  3. Настройки")
        print("  0. Выход")
        print()
        choice = input("  Выберите: ").strip()
        if choice == '0':
            if sniper_thread and sniper_thread.is_alive():
                stop_event.set()
                sniper_thread.join()
            print("  Выход...")
            break
        elif choice == '1':
            if sniper_thread and sniper_thread.is_alive():
                print("  [!] Поиск уже запущен!")
                time.sleep(1)
                continue
            stop_event.clear()
            sniper_thread = threading.Thread(target=run_sniper, args=(config, stop_event))
            sniper_thread.daemon = True
            sniper_thread.start()
            print("  [*] Поиск запущен в фоне. Используйте пункт 2 для остановки.")
            time.sleep(2)
        elif choice == '2':
            if sniper_thread and sniper_thread.is_alive():
                stop_event.set()
                sniper_thread.join()
                print("  [*] Поиск остановлен.")
            else:
                print("  [!] Поиск не запущен.")
            time.sleep(1)
        elif choice == '3':
            clear_screen()
            print("""
╔═══════════════════════════════════════╗
║            НАСТРОЙКИ                  ║
╚═══════════════════════════════════════╝
            """)
            try:
                length = input(f"  Длина юзернейма (сейчас {config.get('length', 5)}): ").strip()
                if length:
                    config['length'] = int(length)
                digits = input(f"  Использовать цифры? (д/н, сейчас {'д' if config.get('with_digits', True) else 'н'}): ").strip().lower()
                if digits in ['д', 'да', 'yes', 'y']:
                    config['with_digits'] = True
                elif digits in ['н', 'нет', 'no', 'n']:
                    config['with_digits'] = False
                underscore = input(f"  Использовать подчёркивания? (д/н, сейчас {'д' if config.get('with_underscore', True) else 'н'}): ").strip().lower()
                if underscore in ['д', 'да', 'yes', 'y']:
                    config['with_underscore'] = True
                elif underscore in ['н', 'нет', 'no', 'n']:
                    config['with_underscore'] = False
                prefix = input(f"  Префикс (сейчас '{config.get('prefix', '')}'): ").strip()
                if prefix:
                    config['prefix'] = prefix
                else:
                    config['prefix'] = ""
                suffix = input(f"  Суффикс (сейчас '{config.get('suffix', '')}'): ").strip()
                if suffix:
                    config['suffix'] = suffix
                else:
                    config['suffix'] = ""
                max_res = input(f"  Максимум результатов (сейчас {config.get('max_results', 10)}): ").strip()
                if max_res:
                    config['max_results'] = int(max_res)
                save_config(config)
                print("\n  [+] Настройки сохранены!")
            except:
                print("\n  [!] Ошибка ввода. Настройки не изменены.")
            time.sleep(2)

if __name__ == '__main__':
    try:
        menu()
    except KeyboardInterrupt:
        print("\n[!] Прервано пользователем.")
        sys.exit(0)
