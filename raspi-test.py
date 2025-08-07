from rich.console import Console
from rich.table import Table
import psutil
import time
import os

console = Console()

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()  # 改行などを除去
            temp = int(temp_str) / 1000.0
        return f"{temp:.1f} °C"
    except (FileNotFoundError, ValueError):
        return "N/A"

def draw():
    table = Table(title="システムダッシュボード")

    table.add_column("項目", style="cyan")
    table.add_column("値", style="magenta")

    # メモリ
    mem = psutil.virtual_memory()
    table.add_row("メモリ使用量", f"{mem.used / (1024 ** 2):.1f} MB / {mem.total / (1024 ** 2):.1f} MB")

    # CPU
    table.add_row("CPU使用率", f"{psutil.cpu_percent()} %")

    # CPU温度
    table.add_row("CPU温度", get_cpu_temp())

    # 稼働時間
    uptime_sec = time.time() - psutil.boot_time()
    uptime_min = uptime_sec / 60
    table.add_row("稼働時間", f"{uptime_min:.1f} 分")

    # ストレージ
    disk = psutil.disk_usage("/")
    table.add_row("ストレージ", f"{disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB")

    console.clear()
    console.print(table)

if __name__ == "__main__":
    try:
        while True:
            draw()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold red]終了しました。")
