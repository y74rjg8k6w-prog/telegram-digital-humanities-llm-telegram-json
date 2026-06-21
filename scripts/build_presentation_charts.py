from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from app.analyzer.parser import parse_telegram_export
from app.analyzer.metrics import build_metrics, build_timeseries
from app.analyzer.network import build_network
from app.analyzer.topics import build_topics


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "example_result.json"
OUTPUT_PATH = ROOT / "docs" / "images" / "pilot-results-dashboard.png"


def main() -> None:
    df = parse_telegram_export(DATA_PATH.read_bytes())
    metrics = build_metrics(df)
    timeseries = build_timeseries(df)
    topics = build_topics(df)
    network = build_network(df)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlesize": 15,
            "axes.labelsize": 10,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(14.4, 9), facecolor="#f5f6f2")
    green = "#247b64"
    terracotta = "#b65042"
    blue = "#4267a8"

    monthly = pd.DataFrame(timeseries["monthly"])
    monthly_pivot = monthly.pivot(index="month", columns="sender", values="messages").fillna(0)
    monthly_pivot.plot(kind="bar", ax=axes[0, 0], color=[green, terracotta], width=0.72)
    axes[0, 0].set_title("Активность по месяцам")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Сообщения")
    axes[0, 0].tick_params(axis="x", rotation=0)
    axes[0, 0].legend(title="")

    sender_df = pd.DataFrame(metrics["by_sender"])
    axes[0, 1].bar(sender_df["sender"], sender_df["messages"], color=[green, terracotta])
    axes[0, 1].set_title("Баланс участия: 12 / 12")
    axes[0, 1].set_ylabel("Сообщения")
    axes[0, 1].set_ylim(0, max(sender_df["messages"]) * 1.25)
    for index, value in enumerate(sender_df["messages"]):
        axes[0, 1].text(index, value + 0.35, str(value), ha="center", fontweight="bold")

    top_words = pd.DataFrame(topics["top_words"][:10], columns=["word", "count"]).sort_values("count")
    axes[1, 0].barh(top_words["word"], top_words["count"], color=blue)
    axes[1, 0].set_title("Частотные содержательные слова")
    axes[1, 0].set_xlabel("Частота")

    graph = nx.DiGraph()
    for edge in network["edges"]:
        graph.add_edge(edge["source"], edge["target"], weight=edge["weight"])
    positions = nx.circular_layout(graph)
    widths = [1 + graph[u][v]["weight"] / 3 for u, v in graph.edges()]
    nx.draw_networkx(
        graph,
        positions,
        ax=axes[1, 1],
        node_color=["#d8eee6", "#f2d8d3"],
        edge_color=terracotta,
        node_size=4200,
        width=widths,
        arrowsize=24,
        font_size=11,
        font_weight="bold",
    )
    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=nx.get_edge_attributes(graph, "weight"),
        ax=axes[1, 1],
        font_size=10,
    )
    axes[1, 1].set_title("Структура переходов между авторами")
    axes[1, 1].axis("off")

    for axis in (axes[0, 0], axes[0, 1], axes[1, 0]):
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.18)

    fig.suptitle(
        "Пилотный анализ Telegram-переписки",
        fontsize=24,
        fontweight="bold",
        color="#1e2420",
        y=0.98,
    )
    fig.text(
        0.5,
        0.02,
        "Синтетический корпус: 24 сообщения, 107 дней. Графики проверяют пайплайн, а не описывают реальных людей.",
        ha="center",
        fontsize=11,
        color="#5c665f",
    )
    fig.tight_layout(rect=(0.03, 0.05, 0.97, 0.94), h_pad=3, w_pad=3)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
