import pandas as pd
from textual.widgets import DataTable, Static, TabPane
from textual.app import ComposeResult
from tabs.utils import get_color_tag, get_ascii_bar

META_COLUMNS = [
    ("Техника", "Name"),
    ("Нация",   "Nation"),
    ("БР",      "BR"),
    ("Бои",     "Сыграно игр"),
    ("WR%",     "WR"),
    ("K/S",     "Убийств за возрождение"),
    ("K/D",     "KD"),
    ("META",    "META_SCORE"),
]


class TabMeta(TabPane):
    def __init__(self):
        super().__init__("🏆 META Рейтинг", id="tab_meta")
        self._sort_key = "META_SCORE"
        self._sort_asc = False

    def compose(self) -> ComposeResult:
        yield Static(
            "[dim]Клик по заголовку — сортировка  │  Enter/клик по строке — карточка техники[/]",
            classes="hint-text"
        )
        yield DataTable(id="vehicle_table", cursor_type="row")
        yield Static("", id="vehicle_card", classes="vehicle-card")

    # ── Публичный метод — вызывается из App при обновлении данных ──
    def refresh_data(self, df: pd.DataFrame) -> None:
        self._df = df
        self._redraw_table()
        self.query_one("#vehicle_card").update("")

    # ── Сортировка по клику на заголовок ──
    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.data_table.id != "vehicle_table":
            return
        clean = str(event.label).replace(" ▲", "").replace(" ▼", "").strip()
        df_key = next((dk for lbl, dk in META_COLUMNS if lbl == clean), None)
        if df_key is None:
            return
        if self._sort_key == df_key:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_key = df_key
            self._sort_asc = False
        self._redraw_table()

    # ── Карточка техники по выбору строки ──
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "vehicle_table":
            return
        if not hasattr(self, "_df") or self._df.empty:
            return
        df = self._df.sort_values(by=self._sort_key, ascending=self._sort_asc).reset_index(drop=True)
        if event.cursor_row >= len(df):
            return
        self._show_card(df.iloc[event.cursor_row])

    def _redraw_table(self) -> None:
        table = self.query_one("#vehicle_table")
        table.clear(columns=True)
        table.zebra_stripes = True

        headers = []
        for lbl, dk in META_COLUMNS:
            arrow = (" ▲" if self._sort_asc else " ▼") if dk == self._sort_key else ""
            headers.append(lbl + arrow)
        table.add_columns(*headers)

        if not hasattr(self, "_df") or self._df.empty:
            return

        for _, row in self._df.sort_values(by=self._sort_key, ascending=self._sort_asc).iterrows():
            m = row["META_SCORE"]
            table.add_row(
                f"[bold white]{row['Name']}[/]",
                str(row["Nation"]),
                f"{row['BR']:.1f}",
                f"{int(row['Сыграно игр']):,}",
                f"{row['WR']:.1f}%",
                f"{row['Убийств за возрождение']:.2f}",
                f"{row['KD']:.2f}",
                f"{get_color_tag(m, [75, 55, 40])}{m:.1f}[/]",
            )

    def _show_card(self, row) -> None:
        m    = row.get("META_SCORE", 0)
        farm = row.get("FARM_SCORE", 0)
        col  = get_color_tag(m, [75, 55, 40])
        self.query_one("#vehicle_card").update("\n".join([
            f"━━━ [bold white]{row['Name']}[/] ━━━  "
            f"[dim]{row.get('Nation','')} │ {row.get('Type','')} │ БР {row.get('BR', 0):.1f}[/]",
            "",
            f"  Боёв:      [bold]{int(row.get('Сыграно игр', 0)):,}[/]",
            f"  Байес. WR: [bold]{row.get('Bayesian_WR', row.get('WR', 0)):.1f}%[/]"
            f"  [#3b82f6]{get_ascii_bar(row.get('WR', 0), 100, 20)}[/]",
            f"  K/Spawn:   [bold]{row.get('Убийств за возрождение', 0):.2f}[/]"
            f"  [#84cc16]{get_ascii_bar(row.get('Убийств за возрождение', 0), 5, 20)}[/]",
            f"  K/D:       [bold]{row.get('KD', 0):.2f}[/]"
            f"  [#84cc16]{get_ascii_bar(row.get('KD', 0), 5, 20)}[/]",
            f"  SL/бой:    [#eab308]{int(row.get('SL за игру', 0)):,}[/]   "
            f"RP/бой: [#3b82f6]{int(row.get('RP за игру', 0)):,}[/]   "
            f"Фарм-индекс: [#eab308]{farm:.1f}[/]",
            f"  META:      {col}{m:.1f}[/]  {col}{get_ascii_bar(m, 100, 20)}[/]",
        ]))
