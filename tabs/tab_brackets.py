import pandas as pd
from textual.widgets import DataTable, Static, TabPane
from textual.app import ComposeResult
from tabs.utils import get_color_tag


# Палитра ячеек: META_SCORE → цвет текста
# Пороги: ≥75 зелёный, ≥55 лаймовый, ≥40 жёлтый, иначе красный
_THRESHOLDS = [75, 55, 40]


def _colored_score(score: float) -> str:
    """Возвращает строку вида '[bold #10b981]82.4[/]'."""
    if score <= 0:
        return "[dim]  —  [/]"
    col = get_color_tag(score, _THRESHOLDS)
    return f"{col}{score:>5.1f}[/]"


class TabBrackets(TabPane):
    """
    Вкладка «БР Кронштейны».

    Сводная таблица: строки — диапазоны БР (0–2, 2–4, …, 12+),
    столбцы — нации, значение — средний META_SCORE топ-5 машин
    в этом кронштейне у этой нации.

    Позволяет мгновенно увидеть, в каком диапазоне БР какая нация
    имеет преимущество.
    """

    def __init__(self):
        super().__init__("📊 БР Кронштейны", id="tab_brackets")

    def compose(self) -> ComposeResult:
        yield Static(
            "[dim]Средний META топ-5 машин нации в каждом БР-диапазоне  │"
            "  Зелёный ≥75  Лайм ≥55  Жёлтый ≥40  Красный < 40[/]",
            classes="hint-text"
        )
        yield DataTable(id="bracket_table", cursor_type="row")
        yield Static("", id="bracket_hint", classes="hint-text")

    def refresh_data(self, pivot: pd.DataFrame) -> None:
        table = self.query_one("#bracket_table")
        table.clear(columns=True)
        table.zebra_stripes = True

        hint = self.query_one("#bracket_hint")

        if pivot.empty:
            hint.update("[red]Нет данных для построения кронштейнов.[/]")
            return

        hint.update("")

        nations = list(pivot.columns)

        # Заголовки: «БР» + все нации
        table.add_columns("БР ╲ Нация", *nations)

        # Для каждой строки (кронштейна) находим нацию с максимальным скором
        for bracket_label, row in pivot.iterrows():
            max_score = row.max()

            cells = [f"[bold white]{bracket_label}[/]"]
            for nation in nations:
                score = row[nation]
                cell  = _colored_score(score)
                # Лидера кронштейна выделяем подчёркиванием (жирный + *)
                if score == max_score and max_score > 0:
                    col = get_color_tag(score, _THRESHOLDS)
                    cell = f"{col}[bold]{score:>5.1f}★[/][/]"
                cells.append(cell)

            table.add_row(*cells)

        # Итоговая строка: лучший кронштейн каждой нации
        best_cells = ["[bold dim]Пик[/]"]
        for nation in nations:
            col_data = pivot[nation]
            best_val = col_data.max()
            best_br  = col_data.idxmax() if best_val > 0 else "—"
            col      = get_color_tag(best_val, _THRESHOLDS) if best_val > 0 else "[dim]"
            best_cells.append(
                f"{col}{best_val:.1f}[/]\n[dim]{best_br}[/]" if best_val > 0 else "[dim]—[/]"
            )
        table.add_row(*best_cells)
