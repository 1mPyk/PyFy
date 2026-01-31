import urllib.request
import urllib.error
import requests
import os
import sys
import subprocess
from urllib.parse import urlparse
from win32com.client import Dispatch

# Настройки
CURRENT_VERSION = "1.4.1"
CURRENT_UPDATER_VERSION = "1.4.1"
VERSION_URL = (
    "https://raw.githubusercontent.com/1mPyk/Testmain/refs/heads/main/versionPyFy.txt"
)
UPDATE_URL_FILE_URL = "https://raw.githubusercontent.com/1mPyk/Testmain/refs/heads/main/LatestUpdatePyFy.txt"
LINE = 0

startup_folder = os.path.join(
    os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"
)
shortcut_name = "Updater.lnk"
shortcut_path = os.path.join(startup_folder, shortcut_name)

if not os.path.exists(shortcut_path):
    target = (
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    icon_path = "app.ico"
    if not os.path.exists(icon_path):
        icon_path = target
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = icon_path
    shortcut.save()
else:
    os.remove(shortcut_path)
    target = (
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    icon_path = "app.ico"
    if not os.path.exists(icon_path):
        icon_path = target
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = icon_path
    shortcut.save()


def compare_versions(v1: str, v2: str) -> int:
    a = [int(x) for x in v1.split(".")]
    b = [int(x) for x in v2.split(".")]
    length = max(len(a), len(b))
    a += [0] * (length - len(a))
    b += [0] * (length - len(b))
    for x, y in zip(a, b):
        if x < y:
            return -1
        if x > y:
            return 1
    return 0


def get_latest_version():
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=6) as resp:
            return resp.read().decode("utf-8").strip().splitlines()[0].strip()
    except Exception as e:
        print(f"[Ошибка] Не удалось получить последнюю версию: {e}")
        return None


def get_update_url(line_number=0):  # 0 — первая строка, 1 — вторая и т.д.
    try:
        with urllib.request.urlopen(UPDATE_URL_FILE_URL, timeout=6) as resp:
            lines = [
                line.strip()
                for line in resp.read().decode("utf-8").splitlines()
                if line.strip()
            ]
            if 0 <= line_number < len(lines):
                return lines[line_number]
            else:
                print("[Ошибка] Номер строки вне диапазона.")
                return None
    except Exception as e:
        print(f"[Ошибка] Не удалось получить ссылку на обновление: {e}")
        return None


def download_file(url):
    from urllib.parse import urlparse
    import os
    import requests

    # Получаем имя файла из URL
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename:
        filename = "downloaded_file"

    # Для Dropbox заменяем dl=0 на dl=1
    if "dropbox.com" in url:
        if "dl=0" in url:
            url = url.replace("dl=0", "dl=1")
        elif "dl=1" not in url:
            url += "&dl=1"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}  # Dropbox иногда требует
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"[OK] Файл загружен: {filename}")
        return filename  # Возвращаем реальное имя
    except Exception as e:
        print(f"[Ошибка] Не удалось скачать файл: {e}")
        return None


def get_current_path():
    if getattr(sys, "frozen", False):  # если запущено как .exe (PyInstaller и т.п.)
        return os.path.dirname(sys.executable)
    else:  # если обычный .py
        return os.path.dirname(os.path.abspath(__file__))


current_path = get_current_path()


def create_and_run_updater(zip_name="Update.zip"):
    bat_name = "update.bat"
    update_path = os.path.join(current_path, "PyFy")
    bat_content = f"""@echo off
powershell -nologo -noprofile -command "Expand-Archive '{zip_name}' -DestinationPath '.' -Force"
powershell -Command "Start-Sleep -Seconds 1"
del "{zip_name}"
move "PyFy.exe" "{update_path}"
start "" "%APPDATA%/PyFy/app/Update.exe"
del "%~f0"
"""
    with open(bat_name, "w", encoding="utf-8") as f:
        f.write(bat_content)

    # Запуск батника без консоли
    subprocess.Popen(["cmd", "/c", bat_name], creationflags=subprocess.CREATE_NO_WINDOW)
    print("[OK] Запущен установщик. Программа завершается...")
    sys.exit(0)


def main():
    print(f"Текущая версия: {CURRENT_VERSION}")
    latest_version = get_latest_version()
    if not latest_version:
        return

    print(f"Последняя версия: {latest_version}")

    cmp = compare_versions(CURRENT_VERSION, latest_version)
    if cmp < 0:
        print(f"Доступна новая версия {latest_version}. Загружаю обновление...")
        update_url = get_update_url(line_number=LINE)
        filename = download_file(update_url)
        if filename:
            create_and_run_updater(filename)
        else:
            print("Ссылка на обновление недоступна.")
    elif cmp == 0:
        print("Установлена последняя версия.")
        current_folder = os.path.dirname(os.path.abspath(__name__))
        to_file = os.path.join(current_folder, "PyFy")
        os.startfile(os.path.join(to_file, "PyFy.exe"))
    else:
        print("Локальная версия новее, чем на сервере.")


if __name__ == "__main__":
    main()
