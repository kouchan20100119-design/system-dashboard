from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Sparkline, Static
from textual.containers import Vertical, Horizontal
from textual import events
import psutil
from collections import deque

class HtopApp(App):
    CSS = """
    DataTable {
        height: 1fr;
    }
    Sparkline {
        height: 5;
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.table = DataTable(zebra_stripes=True)
        self.cpu_graph = Sparkline()
        self.cpu_label = Static("CPU Usage (%)")
        self.cpu_history = deque([0.0]*50, maxlen=50)  # 過去50回分

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(self.cpu_label, self.cpu_graph),
        )
        yield self.table
        yield Footer()

    def on_mount(self) -> None:
        # テーブル初期化
        self.table.add_columns("PID", "Name", "CPU %", "Memory %")
        self.update_processes()
        self.update_cpu_graph()
        self.set_interval(1, self.update_processes)     # 1秒ごとにプロセス更新
        self.set_interval(1, self.update_cpu_graph)     # 1秒ごとにCPUグラフ更新

    def update_processes(self) -> None:
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

    def update_cpu_graph(self) -> None:
        cpu = psutil.cpu_percent()
        self.cpu_history.append(cpu)
        self.cpu_graph.values = list(self.cpu_history)  # ← ここを修正

    async def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            await self.action_quit()
        elif event.key == "k":
            if self.table.cursor_row is not None:
                pid = int(self.table.get_row_at(self.table.cursor_row)[0])
                try:
                    psutil.Process(pid).kill()
                    self.update_processes()
                except Exception as e:
                    self.console.print(f"[red]Error killing process {pid}: {e}[/red]")

if __name__ == "__main__":
    HtopApp().run()
