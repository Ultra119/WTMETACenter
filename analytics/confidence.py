from __future__ import annotations

import math

import numpy as np
import pandas as pd

Z_95 = 1.959963984540054

LOW_SAMPLE_BATTLES = 250


def wilson_interval(wins: float, n: float, z: float = Z_95) -> tuple[float, float]:
    if n is None or n <= 0 or not math.isfinite(n):
        return (0.0, 1.0)

    p = min(max(float(wins) / float(n), 0.0), 1.0)
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2.0 * n)) / denom
    margin = (z * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))) / denom

    low = max(0.0, centre - margin)
    high = min(1.0, centre + margin)
    return (low, high)


def add_confidence(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    battles = df["Сыграно игр"].astype(float).clip(lower=0).to_numpy(dtype=float)
    n = battles

    if "Победы" in df.columns:
        w = np.clip(df["Победы"].astype(float).to_numpy(dtype=float), 0.0, n)
    else:
        w = np.clip(n * df["WR"].to_numpy(dtype=float) / 100.0, 0.0, n)

    exact = np.divide(w, n, out=np.zeros_like(n), where=n > 0) * 100.0
    df["WR"] = np.round(np.where(n > 0, exact, df["WR"].to_numpy(dtype=float)), 2)

    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / np.maximum(n, 1e-9)
    p = np.divide(w, n, out=np.zeros_like(n), where=n > 0)

    centre = (p + z2 / (2.0 * np.maximum(n, 1e-9))) / denom
    margin = (
        Z_95 * np.sqrt(p * (1.0 - p) / np.maximum(n, 1e-9) + z2 / (4.0 * np.maximum(n, 1e-9) ** 2))
    ) / denom

    low = np.clip(centre - margin, 0.0, 1.0)
    high = np.clip(centre + margin, 0.0, 1.0)

    no_sample = n <= 0
    low = np.where(no_sample, 0.0, low)
    high = np.where(no_sample, 1.0, high)

    df["WR_CI_LOW"] = np.floor(low * 10000.0) / 100.0
    df["WR_CI_HIGH"] = np.ceil(high * 10000.0) / 100.0
    df["WR_SAMPLE_OK"] = (n >= LOW_SAMPLE_BATTLES).astype(int)

    return df
