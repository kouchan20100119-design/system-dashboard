from rich.console import Console
from rich.table import Table
import psutil
import time
import os
import sys
import termios
import tty
import select

console = Console()

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            temp = int(temp_str) / 1000.0
        return f"{temp:.1f} °C"
    except (FileNotFoundError, ValueError):
        return "N/A"

def make_bar(ratio, length=20):
    filled = int(ratio * length)
    empty = length - filled
    return "[" + "■" * filled + " " * empty + "]"

def getch_noblock():
    # 非ブロッキングで1文字取得
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        if select.select([sys.stdin], [], [], 0.1)[0]:
            ch = sys.stdin.read(1)
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def draw():
    table = Table(title="System Dashboard")

    table.add_column("Item", style="cyan")
    table.add_column("Value", style="cyan")
    table.add_column("Usage", style="green")

    # Memory
    mem = psutil.virtual_memory()
    mem_ratio = mem.used / mem.total
    mem_bar = make_bar(mem_ratio)
    table.add_row(
        "Memory Usage",
        f"{mem.used / (1024 ** 2):.1f} MB / {mem.total / (1024 ** 2):.1f} MB",
        f"{mem_bar} {mem_ratio*100:.1f}%"
    )

    # CPU
    cpu_percent = psutil.cpu_percent()
    cpu_bar = make_bar(cpu_percent / 100)
    table.add_row(
        "CPU Usage",
        f"{cpu_percent} %",
        f"{cpu_bar} {cpu_percent:.1f}%"
    )

    # CPU Frequency
    freq = psutil.cpu_freq()
    if freq:
        freq_str = f"{freq.current:.1f} MHz"
    else:
        freq_str = "N/A"
    table.add_row("CPU Frequency", freq_str, "")

    # CPU Temperature
    table.add_row("CPU Temperature", get_cpu_temp(), "")

    # Uptime
    uptime_sec = time.time() - psutil.boot_time()
    uptime_min = uptime_sec / 60
    uptime_hr = uptime_sec / 3600
    table.add_row("Uptime", f"{uptime_hr:.1f} h ({uptime_min:.1f} min)", "")

    # Task Count
    tasks = len(psutil.pids())
    table.add_row("Running Tasks", f"{tasks}", "")

    # Storage
    disk = psutil.disk_usage("/")
    disk_ratio = disk.used / disk.total
    disk_bar = make_bar(disk_ratio)
    table.add_row(
        "Storage",
        f"{disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB",
        f"{disk_bar} {disk_ratio*100:.1f}%"
    )

    console.clear()
    console.print(table)
    console.print("[yellow]Press q to quit.[/yellow]")

def draw_processes(limit=10):
    proc_table = Table(title="Top Processes", show_lines=True)
    proc_table.add_column("PID", justify="right", style="cyan")
    proc_table.add_column("Name", style="magenta")
    proc_table.add_column("CPU %", justify="right", style="green")
    proc_table.add_column("Mem %", justify="right", style="yellow")

    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append(proc.info)
        except psutil.NoSuchProcess:
            continue

    procs = sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:limit]

    for p in procs:
        proc_table.add_row(
            str(p['pid']),
            p['name'],
            f"{p['cpu_percent']:.1f}",
            f"{p['memory_percent']:.1f}"
        )

    console.print(proc_table)

def kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.kill()
        console.print(f"[red]Process {pid} killed.[/red]")
    except Exception as e:
        console.print(f"[red]Failed to kill {pid}: {e}[/red]")

if __name__ == "__main__":
    try:
        while True:
            console.clear()
            draw()
            draw_processes()

            console.print("[yellow]Press q to quit, k to kill process.[/yellow]")

            ch = getch_noblock()
            if ch == "q":
                break
            elif ch == "k":
                console.print("Enter PID to kill: ", end="")
                pid_str = input()
                if pid_str.isdigit():
                    kill_process(int(pid_str))
                else:
                    console.print("[red]Invalid PID[/red]")

            time.sleep(1)
    except KeyboardInterrupt:
        pass
    console.print("\n[bold red]Finished![/bold red]")
