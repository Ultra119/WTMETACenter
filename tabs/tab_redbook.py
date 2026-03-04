import pandas as pd
from textual.widgets import DataTable, Static, TabPane
from textual.app import ComposeResult


class TabRedbook(TabPane):
    def __init__(self):
        super().__init__("💀 Красная Книга", id="tab_redbook")

    def compose(self) -> ComposeResult:
        yield Static("Техника с наименьшим количеством боев. Забытые герои.", classes="red-hint")
        yield DataTable(id="redbook_table", cursor_type="row")

    def refresh_data(self, df: pd.DataFrame) -> None:
        table = self.query_one("#redbook_table")
        table.clear(columns=True)
        table.add_columns("Техника", "Нация", "БР", "Сыграно боев", "WR%")
        table.zebra_stripes = True

        if df.empty:
            return

        df_dead = df[df["Сыграно игр"] > 0].sort_values(by="Сыграно игр", ascending=True).head(30)
        for _, row in df_dead.iterrows():
            table.add_row(
                f"[dim white]{row['Name']}[/]",
                str(row["Nation"]),
                f"{row['BR']:.1f}",
                f"[bold red]{int(row['Сыграно игр'])}[/]",
                f"{row['WR']:.1f}%",
            )
