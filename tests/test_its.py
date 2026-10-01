import numpy as np
import pandas as pd

from crest.its import analyse, call_times


def _calls(shift, days, per_day, date, seed, slice_share=0.0):
    rng = np.random.default_rng(seed)
    ts, y, grp = [], [], []
    start = pd.Timestamp("2025-03-01")
    for d in range(days):
        for h in rng.integers(0, 24, per_day):
            t = start + pd.Timedelta(days=d, hours=int(h), minutes=int(rng.integers(0, 60)))
            in_slice = rng.random() < slice_share
            p = 0.3 + 0.04 * np.sin(2 * np.pi * h / 24) + (shift if t >= pd.Timestamp(date) and (in_slice or not slice_share) else 0)
            ts.append(t)
            y.append(rng.random() < p)
            grp.append(in_slice)
    return pd.Series(ts), np.array(y), np.array(grp)


def test_level_shift_is_recovered_with_honest_intervals():
    hits, est = 0, []
    for seed in range(12):
        ts, y, _ = _calls(0.1, 24, 400, "2025-03-13", seed)
        out = analyse(ts, y, np.ones(len(y), bool), "2025-03-13")
        assert out["available"] and out["unit"] == "day"
        est.append(out["level"])
        hits += out["level_ci"][0] <= 0.1 <= out["level_ci"][1]
    assert abs(np.mean(est) - 0.1) < 0.015 and hits >= 10


def test_short_series_switch_to_finer_periods_or_refuse():
    ts, y, _ = _calls(0.1, 9, 440, "2025-03-06", 1)
    out = analyse(ts, y, np.ones(len(y), bool), "2025-03-06")
    assert out["available"] and out["unit"] == "6-hour block" and out["season"] == "time-of-day"
    ts, y, _ = _calls(0.1, 3, 40, "2025-03-02", 2)
    assert not analyse(ts, y, np.ones(len(y), bool), "2025-03-02")["available"]


def test_placebos_and_comparison_series():
    ts, y, g = _calls(0.12, 30, 600, "2025-03-18", 3, slice_share=0.5)
    out = analyse(ts, y, g, "2025-03-18", control_mask=~g)
    assert out["placebo_levels"] and out["placebo_large"] <= len(out["placebo_levels"]) // 4
    c = out["control"]
    assert c["level_ci"][0] <= 0 <= c["level_ci"][1] and c["diff_ci"][0] > 0


def test_call_times_prefer_full_timestamps():
    calls = pd.DataFrame({"time_of_interaction": ["2025-11-05 09:30:00", None],
                          "call_date": ["2025-11-05", "2025-11-06"], "call_hour": [9, 14]})
    ts = call_times(calls)
    assert ts.iloc[0] == pd.Timestamp("2025-11-05 09:30:00")
    calls = calls.drop(columns="time_of_interaction")
    assert call_times(calls).iloc[1] == pd.Timestamp("2025-11-06 14:00:00")
