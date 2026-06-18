from app.analyzer.metrics import build_metrics, build_timeseries
from app.analyzer.network import build_network
from app.analyzer.parser import parse_telegram_export
from app.analyzer.topics import build_topics


def analyze_telegram_export(raw: bytes) -> dict:
    df = parse_telegram_export(raw)
    sample = (
        df[["sender", "date", "text"]]
        .tail(8)
        .assign(date=lambda table: table["date"].astype(str))
        .to_dict(orient="records")
    )
    return {
        "metrics": build_metrics(df),
        "timeseries": build_timeseries(df),
        "topics": build_topics(df),
        "network": build_network(df),
        "sample_messages": sample,
    }
