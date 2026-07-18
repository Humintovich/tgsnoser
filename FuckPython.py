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

def typewriter(text, delay=0.001):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write('\n')
    sys.stdout.flush()

def typewriter_lines(lines, delay=0.001):
    for line in lines:
        typewriter(line, delay)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def fullscreen():
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.keybd_event(0x7A, 0, 0, 0)
        else:
            sys.stdout.write("\033[3;0t")
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

RED = "\033[38;2;255;0;0m"
RED_BOLD = "\033[38;2;220;50;50m"
RED_DIM = "\033[38;2;150;0;0m"
RED_BRIGHT = "\033[38;2;255;50;50m"
WHITE = "\033[38;2;255;255;255m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"
HOME = "\033[H"

def red_rain_fullscreen_with_prompt():
    try:
        rows, cols = shutil.get_terminal_size()
    except:
        rows, cols = 30, 80
    drops = [[0] * cols for _ in range(rows)]
    chars = "0123456789"
    prompt = "нажмите любую клавишу для продолжения"
    prompt_x = (cols - len(prompt)) // 2
    prompt_y = rows // 2
    sys.stdout.write("\033[2J\033[H")
    rain_running = True
    while rain_running:
        sys.stdout.write("\033[H")
        for y in range(rows):
            line = ""
            for x in range(cols):
                if y == prompt_y and x >= prompt_x and x < prompt_x + len(prompt):
                    line += " "
                    continue
                if drops[y][x] == 0:
                    drops[y][x] = random.randint(1, 25)
                if random.random() < 0.03:
                    drops[y][x] = 0
                if drops[y][x] > 0:
                    drops[y][x] -= 1
                    char = random.choice(chars)
                    brightness = random.randint(180, 255)
                    line += f"\033[38;2;{brightness};0;0m{char}\033[0m"
                else:
                    line += " "
            print(line)
        sys.stdout.write(f"\033[{prompt_y+1};{prompt_x}H{WHITE}{prompt}{RESET}")
        sys.stdout.flush()
        time.sleep(0.04)
        if kbhit():
            getch()
            rain_running = False
            break

def key_screen():
    global VERSION_MODE
    config = load_config()
    saved_key = config.get("saved_key", "")
    if saved_key:
        if saved_key == BASIC_KEY:
            VERSION_MODE = "basic"
        elif saved_key == PREMIUM_KEY:
            VERSION_MODE = "premium"
        else:
            config["saved_key"] = ""
            save_config(config)
    clear_screen()
    try:
        cols = shutil.get_terminal_size().columns
        rows = shutil.get_terminal_size().rows
    except:
        cols, rows = 80, 24
    box_width = 50
    box_height = 5
    box_x = (cols - box_width) // 2
    box_y = (rows - box_height) // 2
    lines = []
    lines.append(f"{RED_BOLD}   FPYTHONSOCIAL v33.0{RESET}")
    lines.append(f"{RED_DIM}   Введите лицензионный ключ{RESET}")
    lines.append(f"{RED_DIM}   BASIC или PREMIUM{RESET}")  # Изменено
    for line in lines:
        spaces = (cols - len(line)) // 2
        if spaces < 0:
            spaces = 0
        typewriter(" " * spaces + line, 0.001)
    for row in range(box_height):
        sys.stdout.write(f"\033[{box_y + row};{box_x+1}H")
        if row == 0 or row == box_height - 1:
            sys.stdout.write(f"{RED_DIM}" + "═" * box_width + f"{RESET}")
        else:
            sys.stdout.write(f"{RED_DIM}" + " " + " " * (box_width - 2) + " " + f"{RESET}")
    sys.stdout.flush()
    prompt_y = box_y + 2
    prompt_x = (cols - len("Введите ключ: ")) // 2
    sys.stdout.write(f"\033[{prompt_y};{prompt_x+1}H{RED_BOLD}Введите ключ: {RESET}")
    sys.stdout.flush()
    attempt = 0
    while attempt < 3:
        key = input("").strip()
        if key == BASIC_KEY:
            VERSION_MODE = "basic"
            config["saved_key"] = key
            save_config(config)
            print(f"{RED_BRIGHT}Ключ BASIC принят!{RESET}")
            time.sleep(1)
            return True
        elif key == PREMIUM_KEY:
            VERSION_MODE = "premium"
            config["saved_key"] = key
            save_config(config)
            print(f"{RED_BRIGHT}Ключ PREMIUM принят!{RESET}")
            time.sleep(1)
            return True
        else:
            attempt += 1
            print(f"{RED}Неверный ключ. Попытка {attempt}/3.{RESET}")
            time.sleep(1)
            clear_screen()
            key_screen()
            return False
    print(f"{RED}Превышено количество попыток. Выход.{RESET}")
    sys.exit(1)

def print_header(first_show=False):
    clear_screen()
    try:
        cols = shutil.get_terminal_size().columns
    except:
        cols = 80
    logo = r"""
██████╗██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗███████╗ ██████╗ ██████╗██╗ █████╗ ██╗     
██╔════╝██╔══██╗╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██║██╔══██╗██║     
█████╗  ██████╔╝ ╚████╔╝    ██║   ███████║██║   ██║██╔██╗ ██║███████╗██║     ██║     ██║███████║██║     
██╔══╝  ██╔═══╝   ╚██╔╝     ██║   ██╔══██║██║   ██║██║╚██╗██║╚════██║██║     ██║     ██║██╔══██║██║     
██║     ██║        ██║      ██║   ██║  ██║╚██████╔╝██║ ╚████║███████║╚██████╗╚██████╗██║██║  ██║███████╗
╚═╝     ╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝
"""
    lines = []
    lines.append(f"{RED}{logo}{RESET}")
    lines.append(f"{RED_BOLD}{'═'*60}{RESET}")
    lines.append(f"{RED_BOLD}   FPYTHONSOCIAL v33.0     {RED_DIM}от @PythonSocial{RESET}")
    lines.append(f"{RED_BOLD}{'═'*60}{RESET}")
    lines.append(f"{RED_DIM}   Записей: {len(db.data)} | Файлов: {len(db.files)} | Версия: {VERSION_MODE.upper()}{RESET}")
    lines.append(f"{RED_BOLD}{'═'*60}{RESET}")
    if VERSION_MODE == "basic":
        items = [
            "1.ФИО", "2.Телефон", "3.Email", "4.Адрес", "5.Паспорт",
            "6.IP", "7.Логин", "8.Дата", "9.Авто", "10.СНИЛС",
            "11.ИНН", "12.ОКВЭД", "13.Компания", "14.Должность", "15.Telegram",
            "16.VK", "17.Instagram", "18.Twitter", "19.Домен", "20.Общий"
        ]
    else:
        items = [
            "1.ФИО", "2.Телефон", "3.Email", "4.Адрес", "5.Паспорт",
            "6.IP", "7.Логин", "8.Дата", "9.Авто", "10.СНИЛС",
            "11.ИНН", "12.ОКВЭД", "13.Компания", "14.Должность", "15.Telegram",
            "16.VK", "17.Instagram", "18.Twitter", "19.Домен", "20.Общий",
            "21.Загрузить", "22.Файлы", "23.Очистить", "33.Управ.базами",
            "24.Email-утечки", "25.IP-гео", "26.WHOIS", "27.Телефон-инфо", "28.Username-поиск",
            "29.Пароль-утечки", "30.Комбо", "31.Web-поиск", "32.Спам-кодом",
            "34.Browser Dork",
            "99.Переключить версию"
        ]
    menu_lines = []
    for i in range(0, len(items), 4):
        row = items[i:i+4]
        line = ""
        for item in row:
            line += f"{RED_BOLD}{item:<16}{RESET} "
        line = line.rstrip()
        menu_lines.append(line)
    menu_lines.append("")
    menu_lines.append(f"{RED_DIM}  0-Выход{RESET}")
    menu_lines.append(f"{RED_BOLD}{'═'*60}{RESET}")
    full_text = "\n".join(lines + menu_lines)
    if first_show:
        for line in full_text.split('\n'):
            spaces = (cols - len(line)) // 2
            if spaces < 0:
                spaces = 0
            typewriter(" " * spaces + line, 0.001)
    else:
        for line in full_text.split('\n'):
            spaces = (cols - len(line)) // 2
            if spaces < 0:
                spaces = 0
            sys.stdout.write(" " * spaces + line + "\n")
            sys.stdout.flush()

first_header = True

def switch_version():
    global VERSION_MODE
    clear_screen()
    print(f"{RED_BOLD}=== ПЕРЕКЛЮЧЕНИЕ ВЕРСИИ ==={RESET}")
    print(f"{RED_DIM}Текущая версия: {VERSION_MODE.upper()}{RESET}")
    print(f"{RED}1. BASIC (20 функций){RESET}")
    print(f"{RED}2. PREMIUM (34 функции){RESET}")
    choice = input(f"{RED}Выберите версию: {RESET}").strip()
    config = load_config()
    if choice == '1':
        VERSION_MODE = "basic"
        config["saved_key"] = BASIC_KEY
        save_config(config)
        print(f"{RED_BRIGHT}Переключено на BASIC версию.{RESET}")
    elif choice == '2':
        VERSION_MODE = "premium"
        config["saved_key"] = PREMIUM_KEY
        save_config(config)
        print(f"{RED_BRIGHT}Переключено на PREMIUM версию.{RESET}")
    else:
        print(f"{RED}Неверный выбор.{RESET}")
    time.sleep(1)

def manage_databases():
    global db
    clear_screen()
    print(f"{RED_BOLD}=== УПРАВЛЕНИЕ СОХРАНЁННЫМИ БАЗАМИ ==={RESET}")
    print(f"{RED_DIM}Текущие загруженные файлы:{RESET}")
    for i, f in enumerate(db.files, 1):
        print(f"{RED}[{i}]{RESET} {f}")
    print()
    print(f"{RED_DIM}Сохранённые в конфиге:{RESET}")
    saved, _ = load_config()
    for i, f in enumerate(saved, 1):
        print(f"{RED}[{i}]{RESET} {f}")
    print()
    print(f"{RED}1. Удалить все сохранённые базы и очистить текущие{RESET}")
    print(f"{RED}2. Удалить конкретный файл из сохранённых (по номеру){RESET}")
    print(f"{RED}3. Сохранить текущие базы в конфиг (перезаписать){RESET}")
    print(f"{RED}4. Назад{RESET}")
    choice = input(f"{RED}┌─ Выберите действие: {RESET}").strip()
    if choice == '1':
        save_config([])
        db.data = []
        db.files = []
        db.is_structured = False
        print(f"{RED_BRIGHT}Все базы удалены.{RESET}")
        time.sleep(1)
    elif choice == '2':
        saved, _ = load_config()
        if not saved:
            print(f"{RED}Нет сохранённых баз.{RESET}")
            time.sleep(1)
            return
        idx = input(f"{RED}Введите номер файла для удаления: {RESET}").strip()
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(saved):
                removed = saved.pop(idx)
                save_config(saved)
                if removed in db.files:
                    db.files.remove(removed)
                    db.data = []
                    for f in db.files:
                        db.load(f)
                print(f"{RED_BRIGHT}Файл {removed} удалён из конфига.{RESET}")
            else:
                print(f"{RED}Неверный номер.{RESET}")
            time.sleep(1)
        except:
            print(f"{RED}Неверный ввод.{RESET}")
            time.sleep(1)
    elif choice == '3':
        save_config(db.files)
        print(f"{RED_BRIGHT}Текущие базы сохранены в конфиг.{RESET}")
        time.sleep(1)
    else:
        return

def menu_loop():
    global db, first_header
    print_header(first_header)
    first_header = False
    while True:
        choice = input(f"{RED}┌─ Введите номер команды или запрос:{RESET}\n{RED}└─> {RESET}").strip()
        if choice == '0':
            break
        elif choice == '99':
            switch_version()
            print_header()
            continue
        elif choice == '21':
            if VERSION_MODE == "basic":
                print(f"{RED}Функция недоступна в BASIC версии.{RESET}")
                time.sleep(1)
                print_header()
                continue
            fp = input("Путь к файлу: ").strip()
            if db.load(fp):
                print(f"Загружено. Всего: {len(db.data)}")
                saved, _ = load_config()
                if fp not in saved:
                    saved.append(fp)
                    save_config(saved)
            time.sleep(1)
            print_header()
            continue
        elif choice == '22':
            print("Файлы:")
            for f in db.files:
                print(f"  {f}")
            print(f"Всего записей: {len(db.data)}")
            time.sleep(1)
            print_header()
            continue
        elif choice == '23':
            db.data = []
            db.files = []
            db.is_structured = False
            save_config([])
            print("База очищена и сохранённые удалены.")
            time.sleep(1)
            print_header()
            continue
        elif choice == '33':
            if VERSION_MODE == "basic":
                print(f"{RED}Функция недоступна в BASIC версии.{RESET}")
                time.sleep(1)
                print_header()
                continue
            manage_databases()
            print_header()
            continue
        elif choice == '34':
            if VERSION_MODE == "basic":
                print(f"{RED}Функция недоступна в BASIC версии.{RESET}")
                time.sleep(1)
                print_header()
                continue
            print(f"{RED_BOLD}=== BROWSER DORK ==={RESET}")
            print(f"{RED}1. ФИО\n2. Телефон\n3. Email\n4. Адрес\n5. Свой запрос{RESET}")
            dork_choice = input(f"{RED}┌─ Выберите тип: {RESET}").strip()
            types = {'1':'name', '2':'phone', '3':'email', '4':'address', '5':'custom'}
            data_type = types.get(dork_choice, 'custom')
            if data_type == 'custom':
                query = input(f"{RED}Введите запрос: {RESET}").strip()
            else:
                query = input(f"{RED}Введите данные для поиска: {RESET}").strip()
            if query:
                google_dork(data_type, query)
            input("Нажмите Enter...")
            print_header()
            continue
        elif choice in ['24','25','26','27','28','29','30','31','32']:
            if VERSION_MODE == "basic":
                print(f"{RED}Функция недоступна в BASIC версии.{RESET}")
                time.sleep(1)
                print_header()
                continue
            if choice == '24':
                email = input("Введите email: ").strip()
                if email:
                    print(check_email_breach(email))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '25':
                ip = input("Введите IP: ").strip()
                if ip:
                    print(get_ip_info(ip))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '26':
                domain = input("Введите домен (example.com): ").strip()
                if domain:
                    print(whois_domain(domain))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '27':
                phone = input("Введите номер телефона (+79991234567): ").strip()
                if phone:
                    print(get_phone_info(phone))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '28':
                username = input("Введите username: ").strip()
                if username:
                    print(search_username_all(username))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '29':
                password = input("Введите пароль: ").strip()
                if password:
                    print(check_password_breach(password))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '30':
                email = input("Email (или Enter): ").strip() or None
                phone = input("Телефон (или Enter): ").strip() or None
                ip = input("IP (или Enter): ").strip() or None
                if email or phone or ip:
                    print(combined_analysis(email, phone, ip))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '31':
                query = input("Введите запрос для поиска: ").strip()
                if query:
                    print(search_web(query))
                input("Нажмите Enter...")
                print_header()
                continue
            elif choice == '32':
                phone = input("Введите номер для спама кодом (+79991234567): ").strip()
                if phone:
                    count = int(input("Количество запросов (по умолчанию 50): ") or "50")
                    print(spam_code_to_phone(phone, count))
                input("Нажмите Enter...")
                print_header()
                continue
        if choice.isdigit() and 1 <= int(choice) <= 20:
            if not db.data:
                print("База пуста! Загрузите файл (21).")
                time.sleep(1)
                print_header()
                continue
            types_map = {
                '1':'name','2':'phone','3':'email','4':'address','5':'passport',
                '6':'all','7':'all','8':'all','9':'all','10':'all',
                '11':'all','12':'all','13':'all','14':'all','15':'all',
                '16':'all','17':'all','18':'all','19':'all','20':'all'
            }
            st = types_map.get(choice, 'all')
            query = input(f"{RED}┌─ Введите запрос:{RESET}\n{RED}└─> {RESET}").strip()
            if not query:
                print_header()
                continue
            results = db.search(query, st)
            print(f"\n{RED_BOLD}=== Результаты по '{query}' ({len(results)} записей) ==={RESET}")
            if not results:
                print(f"{RED_DIM}Ничего не найдено.{RESET}")
            else:
                for i, record in enumerate(results[:30], 1):
                    print(f"{RED}[{i:2}]{RESET}")
                    if isinstance(record, dict):
                        print(format_record(record))
                    else:
                        print(record)
                    print()
                if len(results) > 30:
                    print(f"{RED_DIM}... и ещё {len(results)-30} записей.{RESET}")
            print(f"{RED_BOLD}{'═'*60}{RESET}")
            input(f"{RED_DIM}Нажмите Enter для продолжения...{RESET}")
            print_header()
            continue
        else:
            print(f"{RED}Неверный выбор.{RESET}")
            time.sleep(1)
            print_header()
            continue

if __name__ == '__main__':
    try:
        config = load_config()
        for path in config.get("databases", []):
            if os.path.exists(path):
                db.load(path)
                print(f"Автозагрузка: {path}")
        fullscreen()
        red_rain_fullscreen_with_prompt()
        key_screen()
        menu_loop()
        print("Выход из программы.")
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        input("Нажмите Enter для завершения...")
