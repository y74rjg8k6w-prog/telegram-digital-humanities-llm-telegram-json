from pathlib import Path

from app.analyzer.pipeline import analyze_telegram_export


def test_example_export_produces_expected_metrics() -> None:
    raw = Path("data/example_result.json").read_bytes()
    result = analyze_telegram_export(raw)

    assert result["metrics"]["total_messages"] == 24
    assert result["metrics"]["participants"] == ["Участник A", "Участник B"]
    assert result["metrics"]["reciprocity_score"] == 1.0
    assert len(result["timeseries"]["monthly"]) == 8
    assert result["topics"]["top_words"]
    assert result["network"]["edges"]
    assert all(0 <= node["centrality"] <= 1 for node in result["network"]["nodes"])
