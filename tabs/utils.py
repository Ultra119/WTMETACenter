def get_color_tag(val: float, thresholds: list) -> str:
    if val >= thresholds[0]: return "[bold #10b981]"
    if val >= thresholds[1]: return "[#84cc16]"
    if val >= thresholds[2]: return "[#eab308]"
    return "[#ef4444]"


def get_ascii_bar(val: float, max_val: float, length: int = 15) -> str:
    fill = int((val / max_val) * length) if max_val > 0 else 0
    fill = min(fill, length)
    return "█" * fill + "░" * (length - fill)
