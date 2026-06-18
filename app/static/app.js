const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const fileInput = document.getElementById("fileInput");
const analyzeButton = document.getElementById("analyzeButton");
const statusNode = document.getElementById("status");
const resultsNode = document.getElementById("results");
let dailyChart;

fileInput.addEventListener("change", () => {
  statusNode.textContent = fileInput.files[0]?.name || "Файл не выбран";
});

analyzeButton.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    statusNode.textContent = "Выбери result.json";
    return;
  }

  const form = new FormData();
  form.append("file", file);
  analyzeButton.disabled = true;
  statusNode.textContent = "Анализирую файл...";

  try {
    const response = await fetch("/api/analyze", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Ошибка анализа");
    }
    renderResults(data);
    statusNode.textContent = "Готово";
  } catch (error) {
    statusNode.textContent = error.message;
  } finally {
    analyzeButton.disabled = false;
  }
});

function renderResults(data) {
  resultsNode.classList.remove("hidden");
  renderMetrics(data.metrics);
  renderDailyChart(data.timeseries.daily);
  renderWords(data.topics.top_words);
  renderSenders(data.metrics.by_sender, data.topics.tfidf_by_sender);
  renderNetwork(data.network);
  document.getElementById("summary").textContent = data.llm_summary.text;
}

function renderMetrics(metrics) {
  const items = [
    ["Сообщений", metrics.total_messages],
    ["Дней", metrics.days],
    ["Сообщений в день", metrics.messages_per_day],
    ["Индекс близости", `${metrics.closeness_index}/100`],
    ["Взаимность", metrics.reciprocity_score],
    ["Участников", metrics.participants.length],
    ["Старт", new Date(metrics.date_start).toLocaleDateString("ru-RU")],
    ["Финиш", new Date(metrics.date_end).toLocaleDateString("ru-RU")],
  ];
  document.getElementById("metricsGrid").innerHTML = items
    .map(([label, value]) => `<div class="metric"><strong>${escapeHtml(String(value))}</strong><span>${escapeHtml(label)}</span></div>`)
    .join("");
}

function renderDailyChart(rows) {
  const labels = [...new Set(rows.map((row) => row.day))];
  const senders = [...new Set(rows.map((row) => row.sender))];
  const colors = ["#247b64", "#b65042", "#4267a8", "#8a6a23"];
  const datasets = senders.map((sender, index) => ({
    label: sender,
    data: labels.map((day) => rows.find((row) => row.day === day && row.sender === sender)?.messages || 0),
    borderColor: colors[index % colors.length],
    backgroundColor: colors[index % colors.length],
    tension: 0.25,
  }));

  if (dailyChart) dailyChart.destroy();
  dailyChart = new Chart(document.getElementById("dailyChart"), {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } },
      scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { beginAtZero: true } },
    },
  });
}

function renderWords(words) {
  document.getElementById("topWords").innerHTML = words
    .map(([word, count]) => `<span class="tag">${escapeHtml(word)} · ${count}</span>`)
    .join("");
}

function renderSenders(senders, tfidf) {
  document.getElementById("senders").innerHTML = senders
    .map((sender) => {
      const terms = (tfidf[sender.sender] || []).slice(0, 5).map(([term]) => term).join(", ");
      return `<div class="sender-row">
        <div><strong>${escapeHtml(sender.sender)}</strong><br><small>TF-IDF: ${escapeHtml(terms || "нет данных")}</small></div>
        <div>${sender.messages} msg</div>
      </div>`;
    })
    .join("");
}

function renderNetwork(network) {
  const edges = network.edges
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 12)
    .map((edge) => `<div class="edge">${escapeHtml(edge.source)} → ${escapeHtml(edge.target)}: ${edge.weight}</div>`)
    .join("");
  document.getElementById("network").innerHTML = edges || "Недостаточно переходов для графа.";
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}
