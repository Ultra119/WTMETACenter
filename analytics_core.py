import os
import json
import pandas as pd
import numpy as np
import re
from logger import log_debug

# ─────────────────────────────────────────────
# Дефолтные веса (используются если settings.json недоступен)
# ─────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "meta_weights": {
        "wr": 0.4,
        "ks": 0.4,
        "kd": 0.2
    },
    "low_battles_threshold": 50,
    "low_battles_penalty":   0.7,
    "top_nations_vehicles":  5
}


class AnalyticsCore:
    def __init__(self):
        self.full_df    = pd.DataFrame()
        self.display_df = pd.DataFrame()
        self.nation_stats = pd.DataFrame()
        self.settings   = self._load_settings()

    # ─────────────────────────────────────────────
    # Загрузка настроек из settings.json
    # ─────────────────────────────────────────────
    def _load_settings(self) -> dict:
        settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "settings.json"
        )
        if not os.path.exists(settings_path):
            # Создаём файл с дефолтами, чтобы пользователь мог редактировать
            try:
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=4)
                log_debug("settings.json создан с дефолтными значениями.")
            except Exception as e:
                log_debug(f"Не удалось создать settings.json: {e}")
            return dict(DEFAULT_SETTINGS)

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Мержим с дефолтами: если в файле нет ключа — берём дефолт
            merged = dict(DEFAULT_SETTINGS)
            merged.update(loaded)
            # Для вложенного словаря meta_weights — тоже мержим
            merged["meta_weights"] = {
                **DEFAULT_SETTINGS["meta_weights"],
                **loaded.get("meta_weights", {})
            }
            log_debug(f"settings.json загружен: {merged}")
            return merged
        except Exception as e:
            log_debug(f"Ошибка чтения settings.json, используются дефолты: {e}")
            return dict(DEFAULT_SETTINGS)

    def reload_settings(self):
        """Перечитать settings.json без перезагрузки данных (вызывается из GUI)."""
        self.settings = self._load_settings()

    # ─────────────────────────────────────────────
    # Загрузка данных
    # ─────────────────────────────────────────────
    def load_data_recursive(self):
        with open("debug_log.txt", "w", encoding="utf-8") as f:
            f.write("=== ЗАПУСК WT META CENTER v5.0 ===\n")

        all_data   = []
        script_dir = os.path.dirname(os.path.abspath(__file__))

        for root, dirs, files in os.walk(script_dir):
            for filename in files:
                if not filename.endswith('.json') or filename == 'settings.json':
                    continue

                rel_path     = os.path.relpath(root, script_dir)
                vehicle_type = "Uncategorized" if rel_path == "." else rel_path.split(os.sep)[0]

                name_parts = filename.replace('.json', '').split('_')
                nation = name_parts[0] if len(name_parts) > 0 else "Unknown"
                mode   = name_parts[1] if len(name_parts) > 1 else "Unknown"

                try:
                    full_path = os.path.join(root, filename)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry in data:
                            entry['Type']   = vehicle_type
                            entry['Nation'] = nation
                            entry['Mode']   = mode
                        all_data.extend(data)
                except Exception as e:
                    log_debug(f"Ошибка файла {filename}: {e}")

        if not all_data:
            return False

        self.full_df = pd.DataFrame(all_data)
        self._clean_data()
        return True

    # ─────────────────────────────────────────────
    # Очистка данных
    # ─────────────────────────────────────────────
    def _clean_data(self):
        df = self.full_df

        cols_to_clean = [
            'Сыграно игр', 'Победы', 'Возрождения', 'Смерти',
            'Наземные убийства', 'Воздушные убийства', 'Убийств за возрождение'
        ]
        for col in cols_to_clean:
            if col in df.columns:
                s = df[col].astype(str)
                s = s.str.replace(',', '', regex=False)
                s = s.map(lambda v: '0' if v.strip() in ('N/A', 'None', 'nan', '') else v)
                df[col] = pd.to_numeric(s, errors='coerce').fillna(0)

        for col in ['SL за игру', 'RP за игру']:
            if col in df.columns:
                s = df[col].astype(str)
                s = s.str.replace(',', '', regex=False).str.replace(' ', '', regex=False)
                s = s.map(lambda v: '0' if v.strip() in ('N/A', 'None', 'nan', '') else v)
                df[col] = pd.to_numeric(s, errors='coerce').fillna(0)
            else:
                df[col] = 0.0

        if 'Убийств за смерть' in df.columns:
            s = df['Убийств за смерть'].astype(str)
            s = s.str.replace(',', '.', regex=False)
            s = s.map(lambda v: '0' if v.strip() in ('N/A', 'None', 'nan', '') else v)
            df['KD'] = pd.to_numeric(s, errors='coerce').fillna(0)
        else:
            df['KD'] = 0.0

        if 'Процент побед' in df.columns:
            s = df['Процент побед'].astype(str)
            s = s.str.replace('%', '', regex=False)
            s = s.map(lambda v: '0' if v.strip() in ('N/A', 'None', 'nan', '') else v)
            df['WR'] = pd.to_numeric(s, errors='coerce').fillna(0)
        else:
            df['WR'] = 0.0

        def extract_br_regex(s):
            s = str(s)
            if 'БР' in s:
                try:
                    parts = s.split()
                    idx   = parts.index('БР')
                    if idx + 1 < len(parts):
                        return float(parts[idx + 1])
                except Exception:
                    pass
            simple_float = re.search(r'\b(\d+\.\d+)\b', s)
            if simple_float:
                return float(simple_float.group(1))
            return 0.0

        df['BR'] = df['Rank_Info'].apply(extract_br_regex) if 'Rank_Info' in df.columns else 0.0

        self.full_df = df

    # ─────────────────────────────────────────────
    # Подсчёт мета-рейтинга
    # ─────────────────────────────────────────────
    def calculate_meta(self, filters: dict) -> pd.DataFrame:
        df = self.full_df.copy()
        if df.empty:
            return df

        # ── фильтры до группировки ──────────────────
        if filters['type'] != 'All':
            df = df[df['Type'] == filters['type']]
        if filters['mode'] != 'All/Mixed':
            df = df[df['Mode'] == filters['mode']]
        if filters['search']:
            df = df[df['Name'].str.contains(filters['search'], case=False, na=False)]

        if df.empty:
            return pd.DataFrame()

        group_cols    = ['Name', 'Nation', 'BR', 'Type']
        existing_cols = [c for c in group_cols if c in df.columns]

        # ── FIX 1: groupby + apply ────────────────────────────────────────────
        # Проблема: groupby(existing_cols).apply() кладёт ключи группировки
        # (Name, Nation, BR, Type) в ИНДЕКС результата, а не в колонки.
        # reset_index(drop=True) их выбрасывал → KeyError 'BR'.
        #
        # Решение:
        #   1. _aggregate_modes убирает ключи группировки из возвращаемой Series
        #      (иначе они дублируются как колонки И как индекс).
        #   2. reset_index() без drop=True возвращает ключи обратно в колонки.
        df_grouped = (
            df.groupby(existing_cols, group_keys=True)
              .apply(self._aggregate_modes, include_groups=False)
              .reset_index()
        )

        # ── числовые фильтры (BR, min_battles) ──────
        df_grouped = df_grouped[
            (df_grouped['BR'] >= filters['min_br']) &
            (df_grouped['BR'] <= filters['max_br']) &
            (df_grouped['Сыграно игр'] >= filters['min_battles'])
        ]

        if filters['nation'] != 'All':
            df_grouped = df_grouped[df_grouped['Nation'] == filters['nation']]

        if not df_grouped.empty:
            w   = self.settings["meta_weights"]
            w_wr = w.get("wr", 0.4)
            w_ks = w.get("ks", 0.4)
            w_kd = w.get("kd", 0.2)
            # Нормируем веса на случай если пользователь задал сумму ≠ 1
            w_sum = w_wr + w_ks + w_kd
            if w_sum == 0:
                w_wr, w_ks, w_kd = 0.4, 0.4, 0.2
                w_sum = 1.0

            avg_wr          = df_grouped['WR'].mean()
            median_battles  = df_grouped['Сыграно игр'].median()
            if np.isnan(median_battles) or median_battles == 0:
                median_battles = 10

            df_grouped['Bayesian_WR'] = (
                (df_grouped['Сыграно игр'] * df_grouped['WR']) +
                (median_battles * avg_wr)
            ) / (df_grouped['Сыграно игр'] + median_battles)

            max_ks = df_grouped['Убийств за возрождение'].max()
            if max_ks == 0 or np.isnan(max_ks): max_ks = 1
            max_kd = df_grouped['KD'].max()
            if max_kd == 0 or np.isnan(max_kd): max_kd = 1

            ks_score = (df_grouped['Убийств за возрождение'] / max_ks) * 100
            kd_score = (df_grouped['KD'] / max_kd) * 100
            wr_score = df_grouped['Bayesian_WR']

            df_grouped['META_SCORE'] = (
                (w_wr * wr_score) + (w_ks * ks_score) + (w_kd * kd_score)
            ) / w_sum

            threshold = self.settings.get("low_battles_threshold", 50)
            penalty   = self.settings.get("low_battles_penalty", 0.7)
            df_grouped.loc[df_grouped['Сыграно игр'] < threshold, 'META_SCORE'] *= penalty

            # ── FIX 2: FARM_SCORE считается ПОСЛЕ фильтрации ─────────────────
            # Раньше техника с 1 боем и 100% WR получала завышенный индекс.
            # Теперь df_grouped уже отфильтрован по min_battles.
            df_grouped['FARM_SCORE'] = (
                (df_grouped['SL за игру'] / 1000) * (df_grouped['WR'] / 50)
            )

        self.display_df = df_grouped.round(2)
        self._calculate_nation_dominance()
        return self.display_df

    # include_groups=False означает, что x НЕ содержит колонки-ключи группировки
    # (Name, Nation, BR, Type) — они придут обратно через reset_index().
    # Это предотвращает дублирование колонок в итоговом DataFrame.
    def _aggregate_modes(self, x: pd.DataFrame) -> pd.Series:
        total_battles = x['Сыграно игр'].sum()

        res = x.iloc[0].copy()
        res['Mode'] = 'Mixed'

        if total_battles == 0:
            res['Сыграно игр']            = 0
            res['WR']                     = 0.0
            res['KD']                     = 0.0
            res['Убийств за возрождение'] = 0.0
            res['SL за игру']             = 0.0
            res['RP за игру']             = 0.0
            return res

        res['Сыграно игр']            = total_battles
        res['WR']  = (x['WR']  * x['Сыграно игр']).sum() / total_battles
        res['Убийств за возрождение'] = (
            x['Убийств за возрождение'] * x['Сыграно игр']
        ).sum() / total_battles
        res['KD']  = (x['KD']  * x['Сыграно игр']).sum() / total_battles
        res['SL за игру'] = x['SL за игру'].mean() if 'SL за игру' in x.columns else 0.0
        res['RP за игру'] = x['RP за игру'].mean() if 'RP за игру' in x.columns else 0.0
        return res

    # ─────────────────────────────────────────────
    # Доминирование наций
    # ─────────────────────────────────────────────
    def _calculate_nation_dominance(self):
        if self.display_df.empty:
            self.nation_stats = pd.DataFrame()
            return

        df  = self.display_df.copy()
        top = self.settings.get("top_nations_vehicles", 5)

        def nation_power(g):
            top_vehicles = g.nlargest(top, 'META_SCORE')
            return pd.Series({
                'Power_Score':    top_vehicles['META_SCORE'].mean(),
                'Vehicles_Count': len(g),
                'Best_Vehicle':   top_vehicles.iloc[0]['Name'] if not top_vehicles.empty else "N/A"
            })

        nat_stats = df.groupby('Nation').apply(nation_power, include_groups=False).reset_index()
        self.nation_stats = nat_stats.sort_values(by='Power_Score', ascending=False)

    # ─────────────────────────────────────────────
    # Данные для вкладки Фарм-Сет
    # ─────────────────────────────────────────────
    def get_farm_set(self, target_br: float, nation: str = "All",
                     vehicle_type: str = "All") -> dict:
        """
        Подбирает оптимальный фарм-состав для заданного БР.

        Возвращает словарь с ключами:
          'anchor'    — техника на target_br с лучшим FARM_SCORE (якорь ММ)
          'main_set'  — топ-5 по FARM_SCORE в диапазоне [target_br-1.0 .. target_br]
          'gems'      — «скрытые жемчужины»: техника на [target_br-2.0 .. target_br-1.0)
                        у которой FARM_SCORE > FARM_SCORE якоря
          'by_type'   — лучший фармер по каждому типу техники в диапазоне
          'target_br' — целевой БР
        """
        df = self.display_df.copy()
        if df.empty or 'FARM_SCORE' not in df.columns:
            empty = pd.DataFrame()
            return {'anchor': empty, 'main_set': empty,
                    'gems': empty, 'by_type': empty, 'target_br': target_br}

        if nation != 'All':
            df = df[df['Nation'] == nation]
        if vehicle_type != 'All':
            df = df[df['Type'] == vehicle_type]

        # ── Якорная техника: ровно на target_br (±0.2 для float-погрешности) ──
        anchor_df = df[
            (df['BR'] >= target_br - 0.15) &
            (df['BR'] <= target_br + 0.15)
        ].sort_values('FARM_SCORE', ascending=False)

        anchor_row = anchor_df.head(1)
        anchor_farm = float(anchor_row['FARM_SCORE'].iloc[0]) if not anchor_row.empty else 0.0

        # ── Основной диапазон: [target_br - 1.0 .. target_br] ────────────────
        # Это реалистичный состав — техника, которую можно эффективно
        # использовать в матчах на выбранном БР (разница не ощущается критично)
        main_pool = df[
            (df['BR'] >= target_br - 1.0) &
            (df['BR'] <= target_br + 0.15)
        ].sort_values('FARM_SCORE', ascending=False)

        main_set = main_pool.head(7).copy()

        # Помечаем роль каждого слота
        def assign_role(row):
            if abs(row['BR'] - target_br) <= 0.15:
                return '⚓ Якорь'
            elif row['FARM_SCORE'] >= anchor_farm * 0.9:
                return '💰 Топ-фармер'
            else:
                return '🔄 Резерв'

        if not main_set.empty:
            main_set['Роль'] = main_set.apply(assign_role, axis=1)

        # ── Скрытые жемчужины: диапазон [target-2.0 .. target-1.0) ──────────
        # Техника с предыдущего ранга, у которой FARM_SCORE выше якоря.
        # Это и есть главный инсайт вкладки: иногда лучше взять машину ниже.
        gems_pool = df[
            (df['BR'] >= target_br - 2.0) &
            (df['BR'] < target_br - 1.0 + 0.15)
        ]
        gems = gems_pool[
            gems_pool['FARM_SCORE'] > anchor_farm
        ].sort_values('FARM_SCORE', ascending=False).head(5)

        # ── Лучший фармер по каждому типу техники в основном диапазоне ──────
        if not main_pool.empty and 'Type' in main_pool.columns:
            by_type = (
                main_pool
                .sort_values('FARM_SCORE', ascending=False)
                .groupby('Type', sort=False)
                .first()
                .reset_index()
            )
        else:
            by_type = pd.DataFrame()

        return {
            'anchor':    anchor_row,
            'main_set':  main_set,
            'gems':      gems,
            'by_type':   by_type,
            'target_br': target_br,
        }

    # ─────────────────────────────────────────────
    # Данные для вкладки БР Кронштейны
    # ─────────────────────────────────────────────
    def get_bracket_stats(self) -> pd.DataFrame:
        """
        Возвращает таблицу: по оси строк — БР-кронштейн (0-2, 2-4, …),
        по оси столбцов — нации, значение — средний META_SCORE топ-5 машин
        в данном кронштейне для данной нации.
        """
        if self.display_df.empty:
            return pd.DataFrame()

        df = self.display_df.copy()

        bins   = [0, 2, 4, 6, 8, 10, 12, 14]
        labels = ["0–2", "2–4", "4–6", "6–8", "8–10", "10–12", "12+"]
        df['BR_Bracket'] = pd.cut(
            df['BR'], bins=bins, labels=labels, right=False, include_lowest=True
        )

        def bracket_nation_score(g):
            return g.nlargest(5, 'META_SCORE')['META_SCORE'].mean()

        bracket = (
            df.groupby(['BR_Bracket', 'Nation'], observed=True)
              .apply(bracket_nation_score, include_groups=False)
              .reset_index(name='Score')
        )

        pivot = bracket.pivot(index='BR_Bracket', columns='Nation', values='Score')
        pivot = pivot.fillna(0).round(1)
        return pivot
