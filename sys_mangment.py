import subprocess
import os
import psutil
import pandas as pd
import numpy as np
import subprocess
import platform
import time
import pyttsx3
import sys

def gen_jarvis_eng(text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[5].id)
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 0.6)
    engine.say(text)
    engine.runAndWait()
    del engine


class gen_sys_monitering:
    def ram_usage():
        sys_ram = psutil.virtual_memory()
        used_percent_ram = sys_ram.percent
        free_percent_ram = 100 - sys_ram.percent
        gen_jarvis_eng(f"current ram usage is {used_percent_ram}")
        print(f"current ram usage is {used_percent_ram}")
        # return f'current ram usage is {used_percent_ram}'

    def cpu_usage():
        sys_cpu = psutil.cpu_percent(interval=1)
        gen_jarvis_eng(f"currently cpu using percentage is {sys_cpu}")
        print(f"currently cpu using percentage is {sys_cpu}")
        # return f'currently cpu using percentage is {sys_cpu}'

    def gen_sys_analysis():
        csv_path = "data/sys_usage_data.csv"
        sys_ram = int(psutil.virtual_memory().percent)
        sys_cpu = int(psutil.cpu_percent(interval=1))
        if not os.path.exists(csv_path):
            pd.DataFrame([{"CPU": sys_cpu, "RAM": sys_ram}]).to_csv(csv_path, index=False)
        sys_data = pd.read_csv(csv_path)
        for col, cur in (("CPU", sys_cpu), ("RAM", sys_ram)):
            if col not in sys_data.columns:
                sys_data[col] = cur
            sys_data[col] = (
                pd.to_numeric(sys_data[col], errors="coerce").fillna(cur).astype(int)
            )
        sys_cpu_avg = int(sys_data["CPU"].mean())
        sys_ram_avg = int(sys_data["RAM"].mean())
        if sys_ram > sys_ram_avg:
            gen_jarvis_eng(f"Sir, current RAM usage ({sys_ram}%) is greater than usual average ({sys_ram_avg}%).")
            print(f"Sir, current RAM usage ({sys_ram}%) is greater than usual average ({sys_ram_avg}%).")
        else:
            gen_jarvis_eng(f"RAM usage is OK ({sys_ram}%")
            print(f"RAM usage is OK ({sys_ram}%")
        if sys_cpu > sys_cpu_avg:
            gen_jarvis_eng(f"Sir, current CPU usage ({sys_cpu}%) is greater than usual average ({sys_cpu_avg}%).")
            print(f"Sir, current CPU usage ({sys_cpu}%) is greater than usual average ({sys_cpu_avg}%).")
        else:
            gen_jarvis_eng(f"CPU usage is OK ({sys_cpu}%")
        new_row = pd.DataFrame([{"CPU": sys_cpu, "RAM": sys_ram}])
        sys_data = pd.concat([sys_data, new_row], ignore_index=True)
        sys_data.to_csv(csv_path, index=False)

    # Assistent Function

    def sys_data_management():
        _sys_ram = psutil.virtual_memory()
        ram = _sys_ram.percent
        sys_ram = ram
        sys_cpu = psutil.cpu_percent(interval=1)
        try:
            sys_data = pd.read_csv("data/sys_usage_data.csv")
        except:
            with open("sys_usage_data.csv") as file:
                file.write()
        new_row = pd.DataFrame({"CPU": [sys_cpu], "RAM": [sys_ram]})
        sys_data = pd.concat([sys_data, new_row], ignore_index=True)
        sys_data.to_csv("data/sys_usage_data.csv", index=False)


class gen_os_mangment:
    def gen_shutdown():
        try:
            time.sleep(5)
            print("sir shuting down in 5 seconds")
            gen_jarvis_eng(f"sir system is shutting down in 5 second ")
        except KeyboardInterrupt:
            return
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /s /t 1")
        elif system == "Linux":
            os.system("shutdown now")
        elif system == "Darwin":  # macOS
            os.system("sudo shutdown -h now")
        else:
            print("Unsupported OS")
            # speak here

    def gen_restart():
        try:
            time.sleep(5)
            print("sir restarting system in 5 seconds")
            gen_jarvis_eng(f"sir system is restarting in 5 seconds")
        except KeyboardInterrupt:
            return
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /r /t 1")
        elif system == "Linux":
            os.system("reboot")
        elif system == "Darwin":  # macOS
            os.system("sudo shutdown -r now")
        else:
            print("Unsupported OS")