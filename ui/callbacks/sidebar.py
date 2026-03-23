import json
from dash import Input, Output, State, ALL, ctx, html, no_update, clientside_callback
import dash_bootstrap_components as dbc
from dash import dcc

from ui.helpers import generate_card, CLASS_PREFIX, fmt_type, _NATION_FLAG

_RESULT_WRAP_STYLE = {
    "backgroundColor": "#0f172a",
    "border":          "1px solid #1e3a5f",
    "borderRadius":    "8px",
    "overflow":        "hidden",
    "boxShadow":       "0 8px 32px rgba(0,0,0,0.6)",
    "maxHeight":       "420px",
    "overflowY":       "auto",
}

_RESULT_HEADER_STYLE = {
    "padding":         "6px 14px",
    "backgroundColor": "#0a1628",
    "borderBottom":    "1px solid #1e3a5f",
    "color":           "#475569",
    "fontSize":        "10px",
    "letterSpacing":   "0.1em",
    "textTransform":   "uppercase",
    "userSelect":      "none",
}

_ITEM_BASE = {
    "display":       "flex",
    "alignItems":    "center",
    "gap":           "10px",
    "padding":       "8px 14px",
    "cursor":        "pointer",
    "borderBottom":  "1px solid #0f172a",
    "transition":    "background-color 0.1s",
}


def _result_item(row: dict, index: int) -> html.Div:
    name   = str(row.get("Name",   ""))
    nation = str(row.get("Nation", "")).lower()
    br     = float(row.get("BR",   0) or 0)
    vtype  = str(row.get("Type",   ""))
    vclass = str(row.get("VehicleClass", "Standard"))

    flag   = _NATION_FLAG.get(nation, "🏴")
    prefix = CLASS_PREFIX.get(vclass, "")

    item_id = {"type": "gsearch-item", "index": index}

    return html.Div(
        id=item_id,
        n_clicks=0,
        children=[
            # Левая колонка: имя + нация
            html.Div([
                html.Span(
                    f"{prefix}{name}",
                    style={
                        "color":      "#e2e8f0",
                        "fontWeight": "600",
                        "fontSize":   "12px",
                        "fontFamily": "'JetBrains Mono', monospace",
                    },
                ),
                html.Span(
                    f"{flag} {nation.title()}",
                    style={
                        "color":    "#64748b",
                        "fontSize": "10px",
                        "marginLeft": "6px",
                    },
                ),
            ], style={"flex": "1", "minWidth": "0", "overflow": "hidden",
                      "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),

            # Правая колонка: BR + тип
            html.Div([
                html.Span(
                    f"BR {br:.1f}",
                    style={"color": "#a7f3d0", "fontSize": "11px",
                           "fontFamily": "'JetBrains Mono', monospace"},
                ),
                html.Span(
                    fmt_type(vtype),
                    style={"color": "#475569", "fontSize": "10px",
                           "marginLeft": "8px"},
                ),
            ], style={"flexShrink": "0"}),
        ],
        style=_ITEM_BASE,
    )


def register(app, core) -> None:
    clientside_callback(
        """
        (function() {
            var _timer = null;
            return function(value) {
                if (_timer) clearTimeout(_timer);
                return new Promise(function(resolve) {
                    _timer = setTimeout(function() {
                        resolve(value || '');
                    }, 400);
                });
            };
        })()
        """,
        Output("store-search-debounced", "data"),
        Input("global-search", "value"),
        prevent_initial_call=True,
    )
    @app.callback(
        Output("global-search-results", "children"),
        Output("global-search-results", "style"),
        Input("store-search-debounced", "data"),
        prevent_initial_call=True,
    )
    def render_search_results(query: str):
        """Показывает или скрывает панель результатов в зависимости от запроса."""
        _hidden = {
            "position": "absolute",
            "top":      "calc(100% + 4px)",
            "right":    "0",
            "width":    "360px",
            "zIndex":   "9999",
            "display":  "none",
        }
        _visible = {**_hidden, "display": "block"}

        if not query or len(query.strip()) < 2 or core.full_df.empty:
            return [], _hidden

        hits = core.full_df[
            core.full_df["Name"].str.contains(query.strip(), case=False, na=False)
        ]

        if hits.empty:
            content = html.Div([
                html.Div("🔍 РЕЗУЛЬТАТЫ", style=_RESULT_HEADER_STYLE),
                html.Div(
                    "Ничего не найдено",
                    style={"padding": "12px 14px", "color": "#475569",
                           "fontSize": "12px", "fontStyle": "italic"},
                ),
            ], style=_RESULT_WRAP_STYLE)
            return content, _visible

        dedup_cols = ["Name", "Nation"] if "Nation" in hits.columns else ["Name"]
        hits = hits.drop_duplicates(subset=dedup_cols).head(15)

        rows_ui = [
            html.Div("🔍 РЕЗУЛЬТАТЫ", style=_RESULT_HEADER_STYLE),
        ]
        for i, (_, row) in enumerate(hits.iterrows()):
            rows_ui.append(_result_item(row.to_dict(), i))

        content = html.Div(rows_ui, style=_RESULT_WRAP_STYLE)
        return content, _visible

    @app.callback(
        Output("vehicle-modal",      "is_open",  allow_duplicate=True),
        Output("vehicle-modal-body", "children", allow_duplicate=True),
        Output("store-selected-vehicle", "data", allow_duplicate=True),
        Output("global-search",      "value",    allow_duplicate=True),
        Output("global-search-results", "style", allow_duplicate=True),
        Input({"type": "gsearch-item", "index": ALL}, "n_clicks"),
        State("store-search-debounced", "data"),
        prevent_initial_call=True,
    )
    def open_vehicle_from_search(n_clicks_list, query):
        _hidden_style = {
            "position": "absolute",
            "top":      "calc(100% + 4px)",
            "right":    "0",
            "width":    "360px",
            "zIndex":   "9999",
            "display":  "none",
        }

        if not any(n for n in (n_clicks_list or []) if n):
            return no_update, no_update, no_update, no_update, no_update

        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            return no_update, no_update, no_update, no_update, no_update

        idx = triggered.get("index", 0)

        # Повторяем поиск, чтобы получить ту же строку по индексу
        if not query or core.full_df.empty:
            return no_update, no_update, no_update, no_update, no_update

        hits = core.full_df[
            core.full_df["Name"].str.contains(query.strip(), case=False, na=False)
        ]
        dedup_cols = ["Name", "Nation"] if "Nation" in hits.columns else ["Name"]
        hits = hits.drop_duplicates(subset=dedup_cols).head(15)

        if idx >= len(hits):
            return no_update, no_update, no_update, no_update, no_update

        row  = hits.iloc[idx].to_dict()
        name = str(row.get("Name",   ""))
        nation = str(row.get("Nation", ""))

        # Пробуем обогатить из display_df, затем full_df
        enriched = core.get_vehicle_row(name, nation)
        if enriched is None and not core.full_df.empty:
            mask = core.full_df["Name"] == name
            if nation and "Nation" in core.full_df.columns:
                mask &= core.full_df["Nation"] == nation
            sub = core.full_df[mask]
            enriched = sub.iloc[0].to_dict() if not sub.empty else None

        if enriched is None:
            err = dbc.Alert(
                [html.B("Не найдено: "), f"«{name}»"],
                color="warning", style={"margin": "16px"},
            )
            return True, err, no_update, "", _hidden_style

        selected_json = json.dumps({
            k: (v if not hasattr(v, "item") else v.item())
            for k, v in enriched.items()
            if not isinstance(v, (list, dict))
        })

        # Закрываем dropdown и сбрасываем поле после выбора
        return True, generate_card(enriched), selected_json, "", _hidden_style

    @app.callback(
        Output("sb-type-warning", "children"),
        Input("sb-ground",      "value"),
        Input("sb-air",         "value"),
        Input("sb-large-fleet", "value"),
        Input("sb-small-fleet", "value"),
    )
    def type_warning(ground, air, lf, sf):
        has_ground_air = bool(ground or air)
        has_fleet      = bool(lf or sf)
        none_selected  = not any([ground, air, lf, sf])

        if none_selected:
            return dbc.Alert("⚠️ Не выбран ни один класс техники",
                             color="warning", className="mt-1 p-1",
                             style={"fontSize": "0.72rem"})
        if has_ground_air and has_fleet:
            return dbc.Alert("⚠️ Смешение: флот + наземка/авиация",
                             color="warning", className="mt-1 p-1",
                             style={"fontSize": "0.72rem"})
        return ""
