#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import importlib
import os
import time
import random
import shutil
import re
import json
import base64
import hashlib
import sqlite3
import csv
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus

def install_package(pkg):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', pkg])
        return True
    except Exception as e:
        print(f"Ошибка установки {pkg}: {e}")
        return False

required = ['requests', 'whois', 'phonenumbers']
for pkg in required:
    try:
        importlib.import_module(pkg.replace('-', '_'))
    except ImportError:
        print(f"[+] Устанавливаю: {pkg}...")
        install_package(pkg)

import requests
import whois
import phonenumbers
from phonenumbers import carrier, geocoder, timezone

try:
    import termios
    import tty
    import select
    UNIX = True
except ImportError:
    UNIX = False
    import msvcrt

def getch():
    if not UNIX:
        return msvcrt.getch()
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

def kbhit():
    if not UNIX:
        return msvcrt.kbhit()
    else:
        return sys.stdin in select.select([sys.stdin], [], [], 0)[0]

ENCRYPTED_BASIC = "QkFTSUMyMDI1"
ENCRYPTED_PREMIUM = "UFJFTUlVTjIwMjU="
def decrypt_key(encrypted):
    return base64.b64decode(encrypted).decode('utf-8')
BASIC_KEY = decrypt_key(ENCRYPTED_BASIC)
PREMIUM_KEY = decrypt_key(ENCRYPTED_PREMIUM)

VERSION_MODE = "basic"
CONFIG_FILE = os.path.expanduser("~/.fpythonsocial_config.json")

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

class DB:
    def __init__(self):
        self.data = []
        self.files = []
        self.is_structured = False
    def load(self, fp):
        try:
            ext = os.path.splitext(fp)[1].lower()
            if ext == '.json':
                with open(fp, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    if isinstance(raw, list) and all(isinstance(x, dict) for x in raw):
                        self.data = raw
                        self.is_structured = True
                    else:
                        self.data = [str(x) for x in raw]
            elif ext == '.csv':
                with open(fp, 'r', encoding='utf-8') as f:
                    sample = f.read(1024)
                    f.seek(0)
                    sniffer = csv.Sniffer()
                    has_header = sniffer.has_header(sample)
                    dialect = sniffer.sniff(sample)
                    f.seek(0)
                    if has_header:
                        reader = csv.DictReader(f, dialect=dialect)
                        self.data = list(reader)
                        self.is_structured = True
                    else:
                        reader = csv.reader(f, dialect=dialect)
                        self.data = [" ".join(row) for row in reader]
            elif ext == '.db':
                conn = sqlite3.connect(fp)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    description = cursor.description
                    col_names = [desc[0] for desc in description]
                    for row in rows:
                        record = dict(zip(col_names, row))
                        self.data.append(record)
                conn.close()
                if self.data:
                    self.is_structured = True
            else:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.strip() for line in f if line.strip()]
                self.data = lines
            self.files.append(fp)
            return True
        except Exception as e:
            print(f"Ошибка загрузки {fp}: {e}")
            return False
    def search(self, query, search_type='all'):
        results = []
        q = query.lower().strip()
        if not q:
            return results
        for record in self.data:
            if isinstance(record, dict):
                match = False
                for key, value in record.items():
                    if value is None:
                        continue
                    if search_type == 'phone':
                        clean = re.sub(r'[^0-9+]', '', str(value))
                        if q in clean.lower():
                            match = True
                            break
                    elif search_type == 'email':
                        if '@' in str(value) and q in str(value).lower():
                            match = True
                            break
                    elif search_type == 'name':
                        if q in str(value).lower():
                            match = True
                            break
                    elif search_type == 'address':
                        if any(x in str(value).lower() for x in ['ул','пр','д','кв']) and q in str(value).lower():
                            match = True
                            break
                    else:
                        if q in str(value).lower():
                            match = True
                            break
                if match:
                    results.append(record)
            else:
                if q in str(record).lower():
                    results.append(record)
        return results

db = DB()

def get_phone_info(phone):
    try:
        num = phonenumbers.parse(phone, None)
        country = geocoder.description_for_number(num, "ru")
        operator = carrier.name_for_number(num, "ru")
        tz = timezone.time_zones_for_number(num)
        return f"Страна: {country}\nОператор: {operator}\nЧасовой пояс: {tz}"
    except:
        return "Ошибка парсинга номера."

def spam_code_to_phone(phone, count=50):
    url = "https://my.telegram.org/auth/send_code"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    success = 0
    for i in range(count):
        try:
            data = {'phone': phone, '_': str(int(time.time()*1000)) + str(random.randint(1000,9999))}
            r = requests.post(url, data=data, headers=headers, timeout=5)
            if r.status_code == 200:
                success += 1
        except:
            pass
        if i % 10 == 0:
            print(f"Отправлено {i} запросов, успешно {success}")
        time.sleep(0.5 + random.random()*1.5)
    return f"Готово: {success} из {count}"

def check_email_breach(email):
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        r = requests.get(url, headers={'hibp-api-key': ''}, timeout=10)
        if r.status_code == 200:
            breaches = r.json()
            if breaches:
                return f"Найдено утечек: {len(breaches)}. " + ", ".join([b['Name'] for b in breaches])
            else:
                return "Утечек не найдено."
        elif r.status_code == 404:
            return "Утечек не найдено."
        else:
            return f"Ошибка API: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"

def get_ip_info(ip):
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return f"IP: {data.get('ip')}\nГород: {data.get('city')}\nРегион: {data.get('region')}\nСтрана: {data.get('country')}\nОрганизация: {data.get('org')}\nПочтовый индекс: {data.get('postal')}\nКоординаты: {data.get('loc')}"
        else:
            return f"Ошибка API: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"

def whois_domain(domain):
    try:
        w = whois.whois(domain)
        out = []
        for k, v in w.items():
            if v:
                out.append(f"{k}: {v}")
        return "\n".join(out[:20])
    except Exception as e:
        return f"Ошибка WHOIS: {e}"

def search_username_all(username):
    sites = {
        'github': f'https://github.com/{username}',
        'twitter': f'https://twitter.com/{username}',
        'instagram': f'https://instagram.com/{username}',
        'vk': f'https://vk.com/{username}',
        'reddit': f'https://reddit.com/user/{username}',
        'youtube': f'https://youtube.com/@{username}',
        'tiktok': f'https://tiktok.com/@{username}',
        'telegram': f'https://t.me/{username}',
        'facebook': f'https://facebook.com/{username}',
        'linkedin': f'https://linkedin.com/in/{username}',
        'pinterest': f'https://pinterest.com/{username}',
        'twitch': f'https://twitch.tv/{username}',
        'spotify': f'https://open.spotify.com/user/{username}',
        'steam': f'https://steamcommunity.com/id/{username}',
        'xbox': f'https://xboxgamertag.com/{username}',
        'psn': f'https://psnprofiles.com/{username}',
        'hackernews': f'https://news.ycombinator.com/user?id={username}',
        'medium': f'https://medium.com/@{username}',
        'quora': f'https://quora.com/profile/{username}',
        'pastebin': f'https://pastebin.com/u/{username}'
    }
    found = []
    for site, url in sites.items():
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                found.append(f"{site}: {url}")
        except:
            pass
    if found:
        return "Найдено на:\n" + "\n".join(found)
    else:
        return "Не найден нигде."

def check_password_breach(password):
    try:
        sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            lines = r.text.splitlines()
            for line in lines:
                if line.startswith(suffix):
                    count = line.split(':')[1]
                    return f"Пароль найден в утечках {count} раз(а)."
            return "Пароль не найден в утечках."
        else:
            return f"Ошибка API: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"

def combined_analysis(email=None, phone=None, ip=None):
    result = []
    if email:
        result.append(f"Email {email}: {check_email_breach(email)}")
    if phone:
        result.append(f"Телефон {phone}: {get_phone_info(phone)}")
    if ip:
        result.append(f"IP {ip}: {get_ip_info(ip)}")
    return "\n\n".join(result)

def search_web(query):
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return "Поиск в Google выполнен. Откройте браузер для просмотра результатов."
        else:
            return f"Ошибка: {r.status_code}"
    except:
        return "Ошибка."

def google_dork(data_type, query):
    dorks = []
    q = quote_plus(query)
    if data_type == 'name':
        dorks = [f'"{query}" site:vk.com', f'"{query}" site:facebook.com', f'"{query}" site:instagram.com', f'"{query}" filetype:pdf']
    elif data_type == 'phone':
        dorks = [f'"{query}" site:avito.ru', f'"{query}" site:youla.ru', f'"{query}" filetype:txt']
    elif data_type == 'email':
        dorks = [f'"{query}" site:github.com', f'"{query}" site:pastebin.com', f'"{query}" filetype:csv']
    elif data_type == 'address':
        dorks = [f'"{query}" site:2gis.ru', f'"{query}" site:yandex.ru/maps']
    else:
        dorks = [f'"{query}"']
    for dork in dorks:
        url = f"https://www.google.com/search?q={quote_plus(dork)}"
        webbrowser.open(url)
        time.sleep(0.5)

def format_record(record):
    if isinstance(record, dict):
        priority = ['фио', 'имя', 'фамилия', 'name', 'fullname', 'fio',
                    'телефон', 'phone', 'tel', 'mobile', 'номер',
                    'email', 'почта', 'mail',
                    'адрес', 'address', 'место', 'location',
                    'паспорт', 'passport', 'серия', 'snils',
                    'дата', 'birth', 'рождение', 'date',
                    'инн', 'inn',
                    'снилс', 'snils']
        sorted_keys = sorted(record.keys(), key=lambda k: next((i for i, p in enumerate(priority) if p in k.lower()), len(priority)))
        out = []
        label_map = {
            'фио': 'ФИО', 'имя': 'Имя', 'фамилия': 'Фамилия', 'name': 'Имя', 'fullname': 'ФИО', 'fio': 'ФИО',
            'телефон': 'Телефон', 'phone': 'Телефон', 'tel': 'Телефон', 'mobile': 'Мобильный', 'номер': 'Номер',
            'email': 'Email', 'почта': 'Email', 'mail': 'Email',
            'адрес': 'Адрес', 'address': 'Адрес', 'место': 'Место', 'location': 'Локация',
            'паспорт': 'Паспорт', 'passport': 'Паспорт', 'серия': 'Серия', 'snils': 'СНИЛС',
            'дата': 'Дата', 'birth': 'Дата рождения', 'рождение': 'Дата рождения', 'date': 'Дата',
            'инн': 'ИНН', 'inn': 'ИНН',
            'снилс': 'СНИЛС', 'snils': 'СНИЛС'
        }
        for key in sorted_keys:
            value = record[key]
            if value is None or value == '':
                continue
            label = None
            for k, v in label_map.items():
                if k in key.lower():
                    label = v
                    break
            if not label:
                label = key.title()
            out.append(f"{label}: {value}")
        return "\n".join(out)
    else:
        return str(record)

def key_screen():
    global VERSION_MODE
    config = load_config()
    saved_key = config.get("saved_key", "")
    if saved_key:
        if saved_key == BASIC_KEY:
            VERSION_MODE = "basic"
            print("🔑 Автовход в BASIC версию.")
            return True
        elif saved_key == PREMIUM_KEY:
            VERSION_MODE = "premium"
            print("🔑 Автовход в PREMIUM версию.")
            return True
        else:
            config["saved_key"] = ""
            save_config(config)

    print("\n" + "="*50)
    print("FPYTHONSOCIAL v33.0")
    print("="*50)
    print("Введите ключ: BASIC2025 или PREMIUM2025")
    attempt = 0
    while attempt < 3:
        key = input("> ").strip()
        if key == BASIC_KEY:
            VERSION_MODE = "basic"
            config["saved_key"] = key
            save_config(config)
            print("✅ Ключ BASIC принят!")
            time.sleep(1)
            return True
        elif key == PREMIUM_KEY:
            VERSION_MODE = "premium"
            config["saved_key"] = key
            save_config(config)
            print("✅ Ключ PREMIUM принят!")
            time.sleep(1)
            return True
        else:
            attempt += 1
            print(f"❌ Неверный ключ. Попытка {attempt}/3.")
    print("❌ Превышено количество попыток.")
    sys.exit(1)

def startup_rain():
    try:
        if os.name != 'nt':
            pass
        print("🌧️ Красный дождь (пропущено для стабильности).")
    except:
        pass

def red_rain_fullscreen_with_prompt():
    pass

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print("██╗  ██╗██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗███████╗ ██████╗ ██████╗██╗ █████╗ ██╗")
    print("██║  ██║██╔══██╗╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██║██╔══██╗██║")
    print("███████║██████╔╝ ╚████╔╝    ██║   ███████║██║   ██║██╔██╗ ██║███████╗██║     ██║     ██║███████║██║")
    print("██╔══██║██╔═══╝   ╚██╔╝     ██║   ██╔══██║██║   ██║██║╚██╗██║╚════██║██║     ██║     ██║██╔══██║██║")
    print("██║  ██║██║        ██║      ██║   ██║  ██║╚██████╔╝██║ ╚████║███████║╚██████╗╚██████╗██║██║  ██║███████╗")
    print("╚═╝  ╚═╝╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝")
    print("="*60)
    print(f"Версия: {VERSION_MODE.upper()}   Записей: {len(db.data)}   Файлов: {len(db.files)}")
    print("="*60)

def menu_loop():
    global db
    while True:
        print_header()
        if VERSION_MODE == "basic":
            items = [
                "1. ФИО", "2. Телефон", "3. Email", "4. Адрес", "5. Паспорт",
                "6. IP", "7. Логин", "8. Дата", "9. Авто", "10. СНИЛС",
                "11. ИНН", "12. ОКВЭД", "13. Компания", "14. Должность", "15. Telegram",
                "16. VK", "17. Instagram", "18. Twitter", "19. Домен", "20. Общий"
            ]
        else:
            items = [
                "1. ФИО", "2. Телефон", "3. Email", "4. Адрес", "5. Паспорт",
                "6. IP", "7. Логин", "8. Дата", "9. Авто", "10. СНИЛС",
                "11. ИНН", "12. ОКВЭД", "13. Компания", "14. Должность", "15. Telegram",
                "16. VK", "17. Instagram", "18. Twitter", "19. Домен", "20. Общий",
                "21. Загрузить файл", "22. Показать файлы", "23. Очистить базу",
                "24. Email-утечки", "25. IP-гео", "26. WHOIS", "27. Телефон-инфо",
                "28. Username-поиск", "29. Пароль-утечки", "30. Комбо",
                "31. Web-поиск", "32. Спам-кодом", "33. Управление базами",
                "34. Browser Dork"
            ]
        for i in range(0, len(items), 4):
            row = items[i:i+4]
            print("   ".join([f"{item:<16}" for item in row]))
        print("\n0. Выход")
        print("-"*60)
        choice = input("Введите номер команды: ").strip()

        if choice == '0':
            break

        if choice == '21' and VERSION_MODE == "premium":
            fp = input("Путь к файлу: ").strip()
            if db.load(fp):
                print("Файл загружен.")
                config = load_config()
                if "databases" not in config:
                    config["databases"] = []
                if fp not in config["databases"]:
                    config["databases"].append(fp)
                save_config(config)
            else:
                print("Ошибка загрузки.")
            input("Нажмите Enter...")
            continue
        elif choice == '22' and VERSION_MODE == "premium":
            print("Загруженные файлы:")
            for f in db.files:
                print(f"  {f}")
            input("Нажмите Enter...")
            continue
        elif choice == '23' and VERSION_MODE == "premium":
            db.data = []
            db.files = []
            config = load_config()
            config["databases"] = []
            save_config(config)
            print("База очищена.")
            input("Нажмите Enter...")
            continue
        elif choice == '33' and VERSION_MODE == "premium":
            print("Управление базами:")
            print("1. Показать сохранённые пути")
            print("2. Удалить все сохранённые")
            subchoice = input("> ").strip()
            if subchoice == '1':
                config = load_config()
                for p in config.get("databases", []):
                    print(p)
            elif subchoice == '2':
                config = load_config()
                config["databases"] = []
                save_config(config)
                print("Сохранённые пути удалены.")
            input("Нажмите Enter...")
            continue
        elif choice in ['24','25','26','27','28','29','30','31','32','34'] and VERSION_MODE == "premium":
            if choice == '24':
                email = input("Email: ")
                if email:
                    print(check_email_breach(email))
            elif choice == '25':
                ip = input("IP: ")
                if ip:
                    print(get_ip_info(ip))
            elif choice == '26':
                domain = input("Домен: ")
                if domain:
                    print(whois_domain(domain))
            elif choice == '27':
                phone = input("Телефон (+79991234567): ")
                if phone:
                    print(get_phone_info(phone))
            elif choice == '28':
                username = input("Username: ")
                if username:
                    print(search_username_all(username))
            elif choice == '29':
                password = input("Пароль: ")
                if password:
                    print(check_password_breach(password))
            elif choice == '30':
                email = input("Email (или Enter): ") or None
                phone = input("Телефон (или Enter): ") or None
                ip = input("IP (или Enter): ") or None
                if email or phone or ip:
                    print(combined_analysis(email, phone, ip))
            elif choice == '31':
                query = input("Запрос: ")
                if query:
                    print(search_web(query))
            elif choice == '32':
                phone = input("Телефон (+79991234567): ")
                if phone:
                    count = int(input("Количество (по умолчанию 50): ") or "50")
                    print(spam_code_to_phone(phone, count))
            elif choice == '34':
                dtype = input("Тип (name/phone/email/address/custom): ")
                query = input("Данные: ")
                if query:
                    google_dork(dtype, query)
            input("Нажмите Enter...")
            continue

        if choice.isdigit() and 1 <= int(choice) <= 20:
            if not db.data:
                print("База пуста. Загрузите файл (Premium) или используйте внешние функции.")
                input("Нажмите Enter...")
                continue
            st_map = {
                '1':'name','2':'phone','3':'email','4':'address','5':'passport',
                '6':'all','7':'all','8':'all','9':'all','10':'all',
                '11':'all','12':'all','13':'all','14':'all','15':'all',
                '16':'all','17':'all','18':'all','19':'all','20':'all'
            }
            st = st_map.get(choice, 'all')
            query = input("Запрос: ").strip()
            if not query:
                continue
            results = db.search(query, st)
            print(f"\nРезультаты по '{query}': ({len(results)} записей)")
            if results:
                for i, rec in enumerate(results[:30], 1):
                    if isinstance(rec, dict):
                        print(f"{i}.")
                        print(format_record(rec))
                        print()
                    else:
                        print(f"{i}. {rec}")
                if len(results) > 30:
                    print(f"... и ещё {len(results)-30} записей.")
            else:
                print("Ничего не найдено.")
            input("Нажмите Enter...")
            continue

        print("Неверный выбор или функция недоступна в вашей версии.")
        time.sleep(1)

if __name__ == '__main__':
    try:
        config = load_config()
        for path in config.get("databases", []):
            if os.path.exists(path):
                db.load(path)
                print(f"Автозагрузка: {path}")
        key_screen()
        menu_loop()
        print("Выход из программы.")
    except KeyboardInterrupt:
        print("\nВыход.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        input("Нажмите Enter для завершения...")
