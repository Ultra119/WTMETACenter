"""
Вкладка «Фарм-Сет» — подбор оптимального состава техники для SL-фарма.

Ключевая идея: высокий БР ≠ лучший фарм. Техника на 0.3–1.0 ниже целевого БР
нередко имеет выше FARM_SCORE из-за более лёгкого матчмейкинга и лучшего WR.
Вкладка показывает это явно, с цифрами.
"""
import pandas as pd
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, TabPane, Input, Button, Select, Label
from textual.containers import Horizontal, Vertical
from tabs.utils import get_ascii_bar, get_color_tag


# ─── Вспомогательные функции рендера ────────────────────────────────────────

def _farm_bar(score: float, max_score: float) -> str:
    """Цветная шкала фарм-индекса."""
    col = get_color_tag(score / max(max_score, 1) * 100, [75, 55, 40])
    bar = get_ascii_bar(score, max_score, 18)
    return f"{col}{bar}[/]"


def _br_badge(br: float, target: float) -> str:
    """
    Визуальная метка БР относительно цели:
      ●  на целевом БР  → белый
      ▼  ниже на ≤1.0   → жёлтый (в диапазоне)
      ▼▼ ниже на >1.0   → красный (скрытая жемчужина)
    """
    diff = target - br
    if diff <= 0.15:
        return f"[bold white]{br:.1f}[/]"
    if diff <= 1.0:
        return f"[#eab308]{br:.1f} ▼{diff:.1f}[/]"
    return f"[#ef4444]{br:.1f} ▼▼{diff:.1f}[/]"


# ─── Вкладка ────────────────────────────────────────────────────────────────

class TabFarmSet(TabPane):
    """📦 Фарм-Сет — оптимальный набор техники для выбранного БР."""

    def __init__(self):
        super().__init__("📦 Фарм-Сет", id="tab_farmset")
        self._max_farm: float = 1.0

    # ── Вёрстка ─────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #eab308]Подбор состава для фарма SL[/]  [dim]│  "
            "Техника из диапазона [target-2.0 … target] сортируется по FARM_SCORE. "
            "Якорь задаёт брекет ММ — остальные слоты заполняются эффективнее.[/]",
            classes="hint-text",
        )

        with Horizontal(id="farmset-controls"):
            with Vertical(classes="ctrl-block"):
                yield Label("Целевой БР:")
                yield Input(value="7.0", id="fs_br_inp", placeholder="0.0–13.0")
            with Vertical(classes="ctrl-block"):
                yield Label("Нация:")
                yield Select([("All", "All")], id="fs_nation_sel", allow_blank=False)
            with Vertical(classes="ctrl-block"):
                yield Label("Тип техники:")
                yield Select([("All", "All")], id="fs_type_sel", allow_blank=False)
            with Vertical(classes="ctrl-block-btn"):
                yield Label(" ")
                yield Button("🔍 Подобрать", id="fs_apply_btn", variant="primary")

        # ── Блок якоря ───────────────────────────────────────────────────────
        yield Static("", id="fs_anchor_info", classes="fs-anchor-info")

        # ── Основной состав ──────────────────────────────────────────────────
        yield Static(
            "⚙️  [bold]Рекомендуемый фарм-состав[/]  "
            "[dim](top-7 по FARM_SCORE в диапазоне target-1.0 … target)[/]",
            classes="fs-section-title",
        )
        yield DataTable(id="fs_main_table", cursor_type="row")

        # ── Скрытые жемчужины ────────────────────────────────────────────────
        yield Static(
            "💎  [bold]Скрытые жемчужины[/]  "
            "[dim](диапазон target-2.0 … target-1.0, FARM_SCORE > якоря — "
            "стоит включить в ротацию)[/]",
            classes="fs-section-title",
        )
        yield DataTable(id="fs_gems_table", cursor_type="row")

        # ── По типу техники ──────────────────────────────────────────────────
        yield Static(
            "🏷️  [bold]Лучший фармер по типу техники[/]",
            classes="fs-section-title",
        )
        yield DataTable(id="fs_type_table", cursor_type="row")

    # ── Инициализация ────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        self._setup_tables()

    def _setup_tables(self) -> None:
        main = self.query_one("#fs_main_table")
        main.zebra_stripes = True
        main.add_columns(
            "Роль", "Техника", "Нация", "БР", "Тип",
            "SL/бой", "WR%", "FARM_SCORE", "Шкала фарма",
        )

        gems = self.query_one("#fs_gems_table")
        gems.zebra_stripes = True
        gems.add_columns(
            "Техника", "Нация", "БР (разница)", "Тип",
            "SL/бой", "WR%", "FARM_SCORE", "Δ к якорю",
        )

        types = self.query_one("#fs_type_table")
        types.zebra_stripes = True
        types.add_columns("Тип", "Техника", "Нация", "БР", "SL/бой", "WR%", "FARM_SCORE")

    # ── Публичный метод — вызывается из App ──────────────────────────────────
    def populate_selects(self, nations: list[str], types: list[str]) -> None:
        """Заполняет локальные селекты данными из core (вызывается из gui.py)."""
        n_sel = self.query_one("#fs_nation_sel")
        n_sel.set_options([("All", "All")] + [(n, n) for n in nations])
        n_sel.value = "All"

        t_sel = self.query_one("#fs_type_sel")
        t_sel.set_options([("All", "All")] + [(t, t) for t in types])
        t_sel.value = "All"

    def refresh_data(self, result: dict) -> None:
        """Принимает результат analytics_core.get_farm_set() и рендерит его."""
        self._render_anchor(result)
        self._render_main(result)
        self._render_gems(result)
        self._render_by_type(result)

    # ── Рендер секций ────────────────────────────────────────────────────────
    def _render_anchor(self, result: dict) -> None:
        anchor = result['anchor']
        target = result['target_br']
        info   = self.query_one("#fs_anchor_info")

        if anchor.empty:
            info.update(
                f"[#ef4444]⚠  Техника на БР {target:.1f} не найдена в текущих данных. "
                f"Попробуйте изменить фильтры или снизить мин. боёв.[/]"
            )
            return

        row   = anchor.iloc[0]
        farm  = row.get('FARM_SCORE', 0)
        sl    = int(row.get('SL за игру', 0))
        wr    = row.get('WR', 0)
        meta  = row.get('META_SCORE', 0)
        col   = get_color_tag(meta, [75, 55, 40])

        info.update(
            f"⚓  [bold white]{row['Name']}[/]  "
            f"[dim]{row.get('Nation','')} │ {row.get('Type','')} │ БР {row.get('BR',0):.1f}[/]\n"
            f"   SL/бой: [#eab308]{sl:,}[/]   "
            f"WR: [bold]{wr:.1f}%[/]   "
            f"FARM_SCORE: [#eab308]{farm:.2f}[/]   "
            f"META: {col}{meta:.1f}[/]   "
            f"[dim]Якорь задаёт брекет ММ = {target:.1f}. "
            f"Остальные слоты заполняются по FARM_SCORE ↓[/]"
        )
        self._max_farm = max(
            result['main_set']['FARM_SCORE'].max() if not result['main_set'].empty else 1.0,
            result['gems']['FARM_SCORE'].max()     if not result['gems'].empty     else 1.0,
            1.0
        )

    def _render_main(self, result: dict) -> None:
        table  = self.query_one("#fs_main_table")
        table.clear()
        df     = result['main_set']
        target = result['target_br']

        if df.empty:
            return

        for _, row in df.iterrows():
            farm  = row.get('FARM_SCORE', 0)
            role  = row.get('Роль', '—')
            table.add_row(
                role,
                f"[bold white]{row['Name']}[/]",
                str(row.get('Nation', '')),
                _br_badge(row.get('BR', 0), target),
                str(row.get('Type', '')),
                f"[#eab308]{int(row.get('SL за игру', 0)):,}[/]",
                f"{row.get('WR', 0):.1f}%",
                f"[bold]{farm:.2f}[/]",
                _farm_bar(farm, self._max_farm),
            )

    def _render_gems(self, result: dict) -> None:
        table  = self.query_one("#fs_gems_table")
        table.clear()
        df     = result['gems']
        target = result['target_br']
        anchor = result['anchor']

        anchor_farm = (
            float(anchor['FARM_SCORE'].iloc[0]) if not anchor.empty else 0.0
        )

        if df.empty:
            # Явно сообщаем пользователю что жемчужин нет — это тоже информация
            return

        for _, row in df.iterrows():
            farm  = row.get('FARM_SCORE', 0)
            delta = farm - anchor_farm
            delta_str = (
                f"[#10b981]+{delta:.2f}[/]" if delta > 0
                else f"[#ef4444]{delta:.2f}[/]"
            )
            table.add_row(
                f"[bold white]{row['Name']}[/]",
                str(row.get('Nation', '')),
                _br_badge(row.get('BR', 0), target),
                str(row.get('Type', '')),
                f"[#eab308]{int(row.get('SL за игру', 0)):,}[/]",
                f"{row.get('WR', 0):.1f}%",
                f"[bold]{farm:.2f}[/]",
                delta_str,
            )

    def _render_by_type(self, result: dict) -> None:
        table  = self.query_one("#fs_type_table")
        table.clear()
        df     = result['by_type']
        target = result['target_br']

        if df.empty:
            return

        for _, row in df.iterrows():
            farm = row.get('FARM_SCORE', 0)
            table.add_row(
                f"[dim]{row.get('Type', '')}[/]",
                f"[bold white]{row['Name']}[/]",
                str(row.get('Nation', '')),
                _br_badge(row.get('BR', 0), target),
                f"[#eab308]{int(row.get('SL за игру', 0)):,}[/]",
                f"{row.get('WR', 0):.1f}%",
                f"[bold]{farm:.2f}[/]",
            )

    # ── Обработчик кнопки (локальная кнопка на вкладке) ─────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "fs_apply_btn":
            return
        event.stop()
        # Запрашиваем пересчёт через App
        self.app.trigger_farmset_update()
