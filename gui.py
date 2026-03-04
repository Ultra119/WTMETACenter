from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, Button, Select, TabbedContent, Static
from textual.containers import Container, Vertical, Horizontal
from analytics_core import AnalyticsCore
from tabs.tab_meta import TabMeta
from tabs.tab_farm import TabFarm
from tabs.tab_nations import TabNations
from tabs.tab_redbook import TabRedbook
from tabs.tab_brackets import TabBrackets
from tabs.tab_farm_set import TabFarmSet


class WarThunderMetaCenter(App):
    CSS_PATH = "style.tcss"
    TITLE    = "WT COMMAND CENTER v5.0 [ULTIMATE EDITION]"

    core = AnalyticsCore()

    # ─────────────────────────────────────────────
    # Вёрстка
    # ─────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            with Vertical(id="sidebar"):
                yield Static("🎛️ ГЛОБАЛЬНЫЕ ФИЛЬТРЫ", classes="panel-title")
                yield Label("Поиск (Название):")
                yield Input(placeholder="Напр. Tiger", id="search_inp")
                yield Label("Тип техники:")
                yield Select([("All", "All")], id="type_select", allow_blank=False)
                yield Label("Режим:")
                yield Select(
                    [("All/Mixed", "All/Mixed"), ("Realistic", "Realistic"),
                     ("Arcade", "Arcade"), ("Sim", "Sim")],
                    value="All/Mixed", id="mode_select", allow_blank=False,
                )
                yield Label("Нация:")
                yield Select([("All", "All")], id="nation_select", allow_blank=False)
                with Horizontal():
                    with Vertical():
                        yield Label("Мин. БР:")
                        yield Input(value="0.0", id="min_br_inp")
                    with Vertical():
                        yield Label("Макс. БР:")
                        yield Input(value="13.0", id="max_br_inp")
                # Метка-предупреждение — скрыта по умолчанию, появляется при ошибке
                yield Static("", id="br_warning", classes="br-warning")
                yield Label("Мин. боев:")
                yield Input(value="50", id="battles_inp")
                yield Button("⚡ АНАЛИЗ ДАННЫХ", id="apply_btn")

            with TabbedContent():
                yield TabMeta()
                yield TabFarm()
                yield TabNations()
                yield TabRedbook()
                yield TabBrackets()
                yield TabFarmSet()

        yield Footer()

    # ─────────────────────────────────────────────
    # Инициализация
    # ─────────────────────────────────────────────
    def on_mount(self) -> None:
        if self.core.load_data_recursive():
            self.notify("Нейро-ядро загружено успешно!", title="Система")
            self._populate_selects()
            self.trigger_update()
        else:
            self.notify("БАЗА ДАННЫХ НЕ НАЙДЕНА!", severity="error", title="КРИТИЧЕСКАЯ ОШИБКА")

    def _populate_selects(self) -> None:
        df = self.core.full_df

        try:
            nations = sorted(df["Nation"].unique().tolist()) if "Nation" in df.columns else []
        except Exception:
            nations = []
        self.query_one("#nation_select").set_options(
            [("All", "All")] + [(n, n) for n in nations]
        )
        self.query_one("#nation_select").value = "All"

        try:
            types = sorted(df["Type"].unique().tolist()) if "Type" in df.columns else []
        except Exception:
            types = []
        self.query_one("#type_select").set_options(
            [("All", "All")] + [(t, t) for t in types]
        )
        self.query_one("#type_select").value = "All"

        # Заполняем локальные селекты вкладки Фарм-Сет теми же данными
        self.query_one(TabFarmSet).populate_selects(nations, types)

    # ─────────────────────────────────────────────
    # Обработчики событий
    # ─────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "apply_btn":
            self.trigger_update()

    # ─────────────────────────────────────────────
    # Парсинг и валидация фильтров
    # ─────────────────────────────────────────────
    def _parse_filters(self) -> dict | None:
        """
        Возвращает dict с фильтрами или None если есть ошибка валидации.
        Ошибки отображаются через notify() и br_warning.
        """
        warning_label = self.query_one("#br_warning")

        try:
            min_br = float(self.query_one("#min_br_inp").value)
            max_br = float(self.query_one("#max_br_inp").value)
        except ValueError:
            self.notify("Мин./Макс. БР должны быть числами!", severity="error")
            warning_label.update("⚠ БР должен быть числом")
            return None

        try:
            min_battles = int(self.query_one("#battles_inp").value)
        except ValueError:
            self.notify("Мин. боёв должно быть целым числом!", severity="error")
            return None

        # ── FIX: Валидация диапазона БР ────────────────────────────────────
        if min_br > max_br:
            msg = f"⚠ Мин. БР ({min_br}) > Макс. БР ({max_br})!"
            self.notify(msg, severity="warning")
            warning_label.update(msg)
            # Автокоррекция: меняем местами
            min_br, max_br = max_br, min_br
            self.query_one("#min_br_inp").value = str(min_br)
            self.query_one("#max_br_inp").value = str(max_br)
            self.notify("БР-диапазон автоматически скорректирован.", severity="warning")
        else:
            warning_label.update("")  # Сброс предупреждения если всё ок

        if min_br < 0:
            self.notify("Мин. БР не может быть отрицательным!", severity="error")
            warning_label.update("⚠ БР не может быть < 0")
            return None

        return {
            "min_br":      min_br,
            "max_br":      max_br,
            "min_battles": min_battles,
            "search":      self.query_one("#search_inp").value.strip(),
            "mode":        self.query_one("#mode_select").value or "All/Mixed",
            "nation":      self.query_one("#nation_select").value or "All",
            "type":        self.query_one("#type_select").value or "All",
        }

    # ─────────────────────────────────────────────
    # Обновление данных → рассылка по табам
    # ─────────────────────────────────────────────
    def trigger_update(self) -> None:
        filters = self._parse_filters()
        if filters is None:
            return

        df = self.core.calculate_meta(filters)

        self.query_one(TabMeta).refresh_data(df)
        self.query_one(TabFarm).refresh_data(df)
        self.query_one(TabNations).refresh_data(self.core.nation_stats)
        self.query_one(TabRedbook).refresh_data(df)
        self.query_one(TabBrackets).refresh_data(self.core.get_bracket_stats())
        self.trigger_farmset_update()

        self.notify("Матрица данных обновлена.", title="Успех")

    # ─────────────────────────────────────────────
    # Отдельный пересчёт для вкладки Фарм-Сет
    # (вызывается и из trigger_update, и из кнопки на самой вкладке)
    # ─────────────────────────────────────────────
    def trigger_farmset_update(self) -> None:
        tab = self.query_one(TabFarmSet)
        try:
            target_br = float(tab.query_one("#fs_br_inp").value)
        except ValueError:
            self.notify("Фарм-Сет: введите корректный БР!", severity="error")
            return

        target_br = max(0.0, min(13.0, target_br))

        nation = tab.query_one("#fs_nation_sel").value or "All"
        vtype  = tab.query_one("#fs_type_sel").value  or "All"

        result = self.core.get_farm_set(target_br, nation, vtype)
        tab.refresh_data(result)
