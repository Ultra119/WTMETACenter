import pandas as pd
from textual.widgets import DataTable, TabPane
from textual.app import ComposeResult
from tabs.utils import get_ascii_bar


class TabFarm(TabPane):
    def __init__(self):
        super().__init__("💰 Экономика (Фарм)", id="tab_farm")

    def compose(self) -> ComposeResult:
        yield DataTable(id="farm_table", cursor_type="row")

    def refresh_data(self, df: pd.DataFrame) -> None:
        table = self.query_one("#farm_table")
        table.clear(columns=True)
        table.add_columns("Техника", "БР", "SL за бой", "RP за бой", "Индекс Фарма", "Шкала Дохода")
        table.zebra_stripes = True

        if df.empty or "SL за игру" not in df.columns:
            return

        df_farm = df.sort_values(by="FARM_SCORE", ascending=False).head(50)
        max_farm = df_farm["FARM_SCORE"].max() or 1

        for _, row in df_farm.iterrows():
            f_score = row["FARM_SCORE"]
            table.add_row(
                f"[bold white]{row['Name']}[/]",
                f"{row['BR']:.1f}",
                f"[#eab308]{int(row['SL за игру']):,}[/]",
                f"[#3b82f6]{int(row['RP за игру']):,}[/]",
                f"{f_score:.1f}",
                f"[#eab308]{get_ascii_bar(f_score, max_farm, 20)}[/]",
            )
