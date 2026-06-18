from __future__ import annotations

import pandas as pd


def build_metrics(df: pd.DataFrame) -> dict:
    first_date = df["date"].min()
    last_date = df["date"].max()
    days = max((last_date - first_date).days + 1, 1)

    by_sender = []
    total_messages = len(df)
    for sender, group in df.groupby("sender", sort=False):
        by_sender.append(
            {
                "sender": sender,
                "messages": int(len(group)),
                "share": round(len(group) / total_messages, 3),
                "avg_words": round(float(group["word_count"].mean()), 1),
                "questions": int(group["has_question"].sum()),
            }
        )

    gaps = df["date"].diff().dt.total_seconds().fillna(0)
    starters = df.loc[gaps > 6 * 60 * 60, "sender"].value_counts().to_dict()

    reply_times = _reply_times(df)
    reciprocity = _reciprocity_score(df)

    return {
        "total_messages": int(total_messages),
        "participants": sorted(df["sender"].unique().tolist()),
        "date_start": first_date.isoformat(),
        "date_end": last_date.isoformat(),
        "days": int(days),
        "messages_per_day": round(total_messages / days, 2),
        "by_sender": by_sender,
        "conversation_starters_after_6h": {str(k): int(v) for k, v in starters.items()},
        "avg_reply_minutes": reply_times,
        "reciprocity_score": reciprocity,
        "closeness_index": _closeness_index(total_messages, days, reciprocity, reply_times),
    }


def build_timeseries(df: pd.DataFrame) -> dict:
    daily = (
        df.assign(day=df["date"].dt.date.astype(str))
        .groupby(["day", "sender"])
        .size()
        .reset_index(name="messages")
    )
    monthly = (
        df.assign(month=df["date"].dt.to_period("M").astype(str))
        .groupby(["month", "sender"])
        .size()
        .reset_index(name="messages")
    )
    return {
        "daily": daily.to_dict(orient="records"),
        "monthly": monthly.to_dict(orient="records"),
    }


def _reply_times(df: pd.DataFrame) -> dict[str, float]:
    result: dict[str, list[float]] = {}
    previous = None
    for row in df.itertuples(index=False):
        if previous is not None and row.sender != previous.sender:
            minutes = (row.date - previous.date).total_seconds() / 60
            if 0 <= minutes <= 24 * 60:
                result.setdefault(row.sender, []).append(minutes)
        previous = row
    return {sender: round(sum(values) / len(values), 1) for sender, values in result.items() if values}


def _reciprocity_score(df: pd.DataFrame) -> float:
    counts = df["sender"].value_counts()
    if len(counts) < 2:
        return 0.0
    top_two = counts.iloc[:2].to_list()
    low, high = min(top_two), max(top_two)
    return round(low / high, 3)


def _closeness_index(total_messages: int, days: int, reciprocity: float, reply_times: dict[str, float]) -> int:
    activity = min(total_messages / max(days, 1) / 20, 1)
    reply_score = 0.5
    if reply_times:
        avg = sum(reply_times.values()) / len(reply_times)
        reply_score = max(0, min(1, 1 - avg / (24 * 60)))
    score = 100 * (0.4 * activity + 0.35 * reciprocity + 0.25 * reply_score)
    return int(round(score))
