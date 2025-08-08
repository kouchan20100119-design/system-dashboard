from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Vertical, Horizontal
from textual import events
import psutil

class HtopBarApp(App):
    CSS = """
    DataTable {
        height: 1fr;
    }
    .bar {
        height: 1;
        width: 40;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.table = DataTable(zebra_stripes=True)
        self.cpu_bars = []
        self.cpu_labels = []

    def compose(self) -> ComposeResult:
        yield Header()
        
        # 複数列に分けてCPUバーを見やすく並べる
        bar_groups = []
        for i in range(psutil.cpu_count(logical=True)):
            label = Static(f"CPU{i}", classes="bar")
            bar = Static("", classes="bar")
            self.cpu_labels.append(label)
            self.cpu_bars.append(bar)
            group = Vertical(label, bar)
            bar_groups.append(group)

        # 例えば4列に分けて表示
        columns = 4
        rows = [bar_groups[i:i+columns] for i in range(0, len(bar_groups), columns)]
        for row in rows:
            yield Horizontal(*row)  # 各行を水平方向に配置

        yield self.table
        yield Footer()


    def on_mount(self) -> None:
        self.table.add_columns("PID", "Name", "CPU %", "Memory %")
        self.update_processes()
        self.set_interval(1, self.update_processes)
        self.set_interval(1, self.update_cpu_bars)
        if self.table.row_count > 0:
            self.table.cursor_type = "row"
            self.table.move_cursor(row=0)

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
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:30]
        for p in processes:
            self.table.add_row(
                str(p['pid']),
                p['name'] or "N/A",
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_percent']:.1f}"
            )
        if self.table.row_count > 0:
            self.table.cursor_type = "row"
            self.table.move_cursor(row=min(selected_row, self.table.row_count - 1))

    async def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            await self.action_quit()

if __name__ == "__main__":
    HtopBarApp().run()
