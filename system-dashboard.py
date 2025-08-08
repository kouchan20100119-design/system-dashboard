from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, DataTable
from textual.reactive import reactive
import psutil
import time

class SystemDashboard(App):

    CSS_PATH = "dashboard.css"

    memory = reactive("")
    uptime = reactive("")
    processes = reactive([])

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static("Memory Usage", id="mem_label"),
                Static("", id="mem"),
                Static("Uptime", id="uptime_label"),
                Static("", id="uptime"),
                id="left"
            ),
            Vertical(
                Static("Processes", id="procs_label"),
                DataTable(id="procs"),
                id="right"
            )
        )

    def on_mount(self):
        self.set_interval(1, self.update_data)

        table = self.query_one("#procs", DataTable)
        table.add_columns("PID", "Name", "CPU %", "MEM %")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def update_data(self):
        # メモリ使用率更新
        mem = psutil.virtual_memory()
        self.query_one("#mem", Static).update(f"{mem.percent}% used of {round(mem.total / 1e9, 2)} GB")

        # uptime更新
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        self.query_one("#uptime", Static).update(f"{uptime_str}")

        # プロセス一覧更新
        table = self.query_one("#procs", DataTable)
        cursor = table.cursor_coordinate  # 現在の選択位置
        selected_pid = None

        # 現在選択されているPIDを記録
        if cursor and cursor[0] < len(table.rows):
            selected_pid = table.get_row_at(cursor[0])[0]

        table.clear()
        proc_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_list.append([
                    str(proc.info['pid']),
                    proc.info['name'],
                    f"{proc.info['cpu_percent']:.1f}",
                    f"{proc.info['memory_percent']:.1f}"
                ])
            except Exception:
                continue
        proc_list.sort(key=lambda x: float(x[2]), reverse=True)  # CPU順に並べる

        for row in proc_list[:50]:  # 上位50件だけ表示
            table.add_row(*row)

        # 選択位置の復元（追従）
        if selected_pid:
            for i, row in enumerate(proc_list[:50]):
                if row[0] == selected_pid:
                    table.cursor_coordinate = (i, 0)
                    break

if __name__ == "__main__":
    SystemDashboard().run()
