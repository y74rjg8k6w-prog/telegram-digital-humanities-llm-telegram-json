from collections import Counter
from math import log

import pandas as pd


RU_STOPWORDS = {
    "а", "без", "бы", "в", "во", "вот", "да", "для", "до", "его", "ее", "если",
    "же", "за", "и", "или", "из", "к", "как", "ко", "ли", "мне", "мы", "на",
    "не", "но", "ну", "о", "об", "он", "она", "они", "по", "при", "с", "со",
    "так", "там", "ты", "у", "уже", "что", "это", "я", "меня", "тебя", "тебе",
    "моя", "мой", "твоя", "твой", "то", "тоже", "еще", "очень", "просто",
}


def build_topics(df: pd.DataFrame, limit: int = 20) -> dict:
    tokens = " ".join(df["clean_text"].tolist()).split()
    freq = Counter(token for token in tokens if len(token) > 2 and token not in RU_STOPWORDS)

    by_sender = {}
    for sender, group in df.groupby("sender", sort=False):
        sender_tokens = " ".join(group["clean_text"].tolist()).split()
        sender_freq = Counter(
            token for token in sender_tokens if len(token) > 2 and token not in RU_STOPWORDS
        )
        by_sender[sender] = sender_freq.most_common(12)

    tfidf = _tfidf_by_sender(df)
    return {
        "top_words": freq.most_common(limit),
        "top_words_by_sender": by_sender,
        "tfidf_by_sender": tfidf,
    }


def _tfidf_by_sender(df: pd.DataFrame) -> dict[str, list[list[object]]]:
    docs = {
        str(sender): _tokens(" ".join(group["clean_text"].tolist()))
        for sender, group in df.groupby("sender", sort=False)
    }
    if not docs:
        return {}

    doc_count = len(docs)
    document_frequency: Counter[str] = Counter()
    for tokens in docs.values():
        document_frequency.update(set(tokens))

    result: dict[str, list[list[object]]] = {}
    for sender, tokens in docs.items():
        counts = Counter(tokens)
        total = max(sum(counts.values()), 1)
        scores = {}
        for term, count in counts.items():
            tf = count / total
            idf = log((doc_count + 1) / (document_frequency[term] + 1)) + 1
            scores[term] = tf * idf
        result[sender] = [
            [term, round(score, 4)]
            for term, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:12]
        ]
    return result


def _tokens(text: str) -> list[str]:
    return [token for token in text.split() if len(token) > 2 and token not in RU_STOPWORDS]
