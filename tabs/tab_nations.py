import pandas as pd
from textual.widgets import DataTable, TabPane
from textual.app import ComposeResult
from tabs.utils import get_color_tag, get_ascii_bar


class TabNations(TabPane):
    def __init__(self):
        super().__init__("🌍 Топ Наций", id="tab_nations")

    def compose(self) -> ComposeResult:
        yield DataTable(id="nation_table", cursor_type="row")

    def refresh_data(self, nation_stats: pd.DataFrame) -> None:
        table = self.query_one("#nation_table")
        table.clear(columns=True)
        table.add_columns("Ранг", "Нация", "Машин", "Лучшая Техника", "Имбовость (Топ-5)")
        table.zebra_stripes = True

        if nation_stats.empty:
            return

        for rank, (_, row) in enumerate(nation_stats.iterrows(), 1):
            score = row["Power_Score"]
            col   = get_color_tag(score, [75, 55, 40])
            table.add_row(
                f"#{rank}",
                f"[bold white]{row['Nation']}[/]",
                f"{int(row['Vehicles_Count'])}",
                str(row["Best_Vehicle"]),
                f"{col}{score:.1f}[/] {col}{get_ascii_bar(score, 100, 20)}[/]",
            )
