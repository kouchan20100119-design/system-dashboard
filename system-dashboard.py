from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Vertical, Horizontal
from textual import events
import psutil
import time


class HtopBarApp(App):
    CSS_PATH = "dashboard.css"  # 外部CSS

    def __init__(self):
        super().__init__()
        self.table = DataTable(zebra_stripes=True)
        self.cpu_bars = []
        self.cpu_labels = []

        # 新しく追加するバー
        self.uptime_box = Static(id="uptime")
        self.cpu_total_bar = Static(id="cpu_total")
        self.mem_bar = Static(id="mem")

    def compose(self) -> ComposeResult:
        yield Header()

    # システムサマリー
        yield Vertical(
        Static("System Summary", classes="section_title"),
        Vertical(
            self.uptime_box,
            self.cpu_total_bar,
            self.mem_bar,
            id="system_summary"
        ),
        id="summary_section"
        )

    # CPUコア使用率
        core_section = []
        for i in range(psutil.cpu_count(logical=True)):
            label = Static(f"CPU{i}", classes="core_label")
            bar = Static("", classes="core_bar")
            self.cpu_labels.append(label)
            self.cpu_bars.append(bar)
            core_section.append(Vertical(label, bar))
        yield Horizontal(
            Static("CPU Core Usage", classes="section_title"),
            *core_section,
            id="cpu_core_section"
        )

    # プロセステーブル
        yield Vertical(
            Static("Top 30 Processes", classes="section_title"),
            self.table,
            id="process_section"
        )

        yield Footer()


    def on_mount(self) -> None:
        self.table.add_columns("PID", "Name", "CPU %", "Memory %")
        self.update_summary()
        self.update_cpu_bars()
        self.update_processes()
        self.set_interval(1, self.update_processes)
        self.set_interval(1, self.update_cpu_bars)
        self.set_interval(1, self.update_summary)
        if self.table.row_count > 0:
            self.table.cursor_type = "row"
            self.table.move_cursor(row=0)

    def update_summary(self):
        # Uptime
        uptime_sec = time.time() - psutil.boot_time()
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_sec))
        self.uptime_box.update(f"[bold]Uptime:[/bold] {uptime_str}")

        # Total CPU usage
        total_cpu = psutil.cpu_percent()
        filled = int(total_cpu // 2)
        empty = 50 - filled
        self.cpu_total_bar.update(
            f"[bold]CPU:[/bold] [green]{'|' * filled}[/green]{' ' * empty} {total_cpu:5.1f}%"
        )

        # Memory usage
        mem = psutil.virtual_memory()
        mem_ratio = mem.used / mem.total
        filled = int(mem_ratio * 50)
        empty = 50 - filled
        self.mem_bar.update(
            f"[bold]MEM:[/bold] [cyan]{'|' * filled}[/cyan]{' ' * empty} {mem_ratio * 100:5.1f}%"
        )

    def update_cpu_bars(self):
        cpu_percents = psutil.cpu_percent(percpu=True)
        for i, (bar, percent) in enumerate(zip(self.cpu_bars, cpu_percents)):
            filled = int(percent // 2)
            empty = 50 - filled
            bar.update(f"[green]{'|' * filled}[/green]{' ' * empty} {percent:5.1f}%")

    def update_processes(self) -> None:
        selected_row = self.table.cursor_row if self.table.cursor_row is not None else 0
        self.table.clear()
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except psutil.NoSuchProcess:
                continue
        processes = sorted(
        processes,
        key=lambda x: (x['cpu_percent'] or 0),
        reverse=True
        )[:30]

        for p in processes:
            cpu = p['cpu_percent'] or 0
            mem = p['memory_percent'] or 0
            self.table.add_row(
            str(p['pid']),
            p['name'] or "N/A",
            f"{cpu:.1f}",
            f"{mem:.1f}"
        )

        if self.table.row_count > 0:
            self.table.cursor_type = "row"
            self.table.move_cursor(row=min(selected_row, self.table.row_count - 1))

    async def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            await self.action_quit()


if __name__ == "__main__":
    HtopBarApp().run()
