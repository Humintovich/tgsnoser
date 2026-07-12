#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import platform

# ===== АВТОУСТАНОВКА БИБЛИОТЕК =====
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_install():
    required = ['pynput', 'pyperclip', 'plyer']
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            print(f"[+] Устанавливаю модуль: {pkg}...")
            install_package(pkg)

try:
    check_and_install()
except Exception as e:
    print(f"[-] Ошибка установки: {e}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# ===== ИМПОРТЫ ПОСЛЕ УСТАНОВКИ =====
import random
from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip
try:
    from plyer import notification
    NOTIFY = True
except:
    NOTIFY = False

# ===== ОСКОРБЛЕНИЯ =====
INSULTS = [
    "Ты настолько тупой, что даже бот умнее тебя.",
    "Твоя мать шлюха, а ты её недостойный сын.",
    "Иди нахуй, петушара, твой IQ ниже плинтуса.",
    "Завали ебало, дебил, ты меня бесишь.",
    "Ты ошибка природы, гандон, удались из чата.",
    "Отец тебя не любил, и я понимаю почему, пидор.",
    "Твои сообщения – это мусор, как и ты сам, хуйло.",
    "Пошёл в жопу, червь, ты ничтожество, сука.",
    "Ты настолько глуп, что это уже клиника, урод ебаный.",
    "Ебать ты лох, даже бот умнее тебя, хуйло.",
    "Ты хуже коронавируса, от тебя нет вакцины.",
    "Рожа твоя – приговор, урод сраный, иди в баню.",
    "Ты как плесень – распространяешься там, где не надо, пидор.",
    "Заткнись, ты даже звуки издаёшь неправильно, гандон.",
    "Ты – бракованный товар, тебя пора списать, сука.",
    "Иди нахуй, ты даже не человек, ты биомусор, урод.",
    "Твоя тупость не знает границ, как и твоё самомнение, пидор.",
    "Ты – продукт инцеста, это видно невооружённым глазом, мудак.",
    "Ебать ты неудачник, даже пустота умнее тебя, гандон.",
    "Ты как грязный носок – все шарахаются, хуйло сраное."
]

def generate_insult():
    return random.choice(INSULTS)

# ===== ОПРЕДЕЛЯЕМ КОМБИНАЦИЮ ДЛЯ ВСТАВКИ =====
is_mac = platform.system() == 'Darwin'
paste_key = Key.cmd if is_mac else Key.ctrl

# ===== ОБРАБОТЧИК КЛАВИШ =====
keyboard_controller = Controller()

def on_press(key):
    try:
        if key.char == '7':
            insult = generate_insult()
            # Копируем в буфер
            pyperclip.copy(insult)
            print(f"\n[+] Оскорбление: {insult}")
            print("[+] Вставляю в активное окно...")
            
            # Имитируем Ctrl+V / Cmd+V для вставки
            with keyboard_controller.pressed(paste_key):
                keyboard_controller.press('v')
                keyboard_controller.release('v')
            
            if NOTIFY:
                try:
                    notification.notify(
                        title="Оскорбление вставлено!",
                        message=insult[:50] + ("..." if len(insult) > 50 else ""),
                        timeout=2
                    )
                except:
                    pass
    except AttributeError:
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        return False

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
def main():
    print("""
╔═══════════════════════════════════════════════════════╗
║   INSULT GENERATOR v3.0                              ║
║   Нажмите 7 – оскорбление сразу вставится в поле    ║
║   ESC – выход                                       ║
╚═══════════════════════════════════════════════════════╝
    """)
    print("[*] Ожидание нажатий...")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Программа завершена.")
    except Exception as e:
        print(f"[-] Ошибка: {e}")
    finally:
        input("Нажмите Enter для выхода...")
