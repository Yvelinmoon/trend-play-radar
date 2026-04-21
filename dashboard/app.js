const state = {
  allTopics: [],
  filteredTopics: [],
};

const DEFAULT_REMOTE_BASE = "https://trend-play-radar-google-trends-bridge.xiyomi-congito-kant999.workers.dev";

const sourceStatus = document.querySelector("#source-status");
const topicList = document.querySelector("#topic-list");
const emptyState = document.querySelector("#empty-state");
const template = document.querySelector("#topic-card-template");
const classificationFilter = document.querySelector("#classification-filter");
const platformFilter = document.querySelector("#platform-filter");
const searchFilter = document.querySelector("#search-filter");
const refreshLiveButton = document.querySelector("#refresh-live");
const loadLatestButton = document.querySelector("#load-latest");
const openReportButton = document.querySelector("#open-report");
const historySelect = document.querySelector("#history-select");
const loadHistoryButton = document.querySelector("#load-history");
const reloadHistoryButton = document.querySelector("#reload-history");
const refreshStatus = document.querySelector("#refresh-status");

const topicCount = document.querySelector("#topic-count");
const highConfidenceCount = document.querySelector("#high-confidence-count");
const averagePriority = document.querySelector("#average-priority");
const lastPublished = document.querySelector("#last-published");
const currentSource = document.querySelector("#current-source");
const historyCount = document.querySelector("#history-count");
const viewMode = document.querySelector("#view-mode");
const sourceComparison = document.querySelector("#source-comparison");
const emptyTitle = document.querySelector("#empty-title");
const emptyDetail = document.querySelector("#empty-detail");

const historyStorageKey = "trend-play-radar:last-history-index-url";

let historyEntries = [];

init();

function init() {
  wireEvents();
  tryAutoLoad();
}

function wireEvents() {
  classificationFilter.addEventListener("change", applyFilters);
  platformFilter.addEventListener("change", applyFilters);
  searchFilter.addEventListener("input", applyFilters);

  refreshLiveButton.addEventListener("click", async () => {
    refreshLiveButton.disabled = true;
    refreshStatus.textContent = "Running a live refresh from the worker...";
    try {
      const payload = await triggerRefresh();
      refreshStatus.textContent = buildRefreshSummary(payload);
      await loadHistoryIndex({ silent: true });
      await loadFromUrl(getLiveReportUrl());
      sourceStatus.textContent = "Loaded the latest refreshed live report.";
    } catch (error) {
      refreshStatus.textContent = formatRefreshError(error);
      if (isNoDataError(error)) {
        clearDashboard("No live data published yet", "Refresh finished without a publishable report yet.");
      }
    } finally {
      refreshLiveButton.disabled = false;
    }
  });

  loadLatestButton.addEventListener("click", async () => {
    const latestUrl = getLiveReportUrl();
    sourceStatus.textContent = "Switching to live report...";
    try {
      await loadFromUrl(latestUrl);
      sourceStatus.textContent = `Loaded live report from ${shortenUrl(latestUrl)}`;
    } catch (error) {
      if (isNoDataError(error)) {
        clearDashboard("No live data published yet", "Use Refresh Live Data to run a manual collection.");
        sourceStatus.textContent = "No live report is available yet.";
      } else {
        sourceStatus.textContent = formatLoadError(latestUrl, error);
      }
    }
  });

  openReportButton.addEventListener("click", () => {
    const url = getLiveReportUrl();
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  });

  loadHistoryButton.addEventListener("click", async () => {
    if (!historySelect.value) return;
    sourceStatus.textContent = `Loading history batch from ${shortenUrl(historySelect.value)}...`;
    try {
      await loadFromUrl(historySelect.value);
    } catch (error) {
      sourceStatus.textContent = formatLoadError(historySelect.value, error);
    }
  });

  reloadHistoryButton.addEventListener("click", () => {
    loadHistoryIndex();
  });
}

async function tryAutoLoad() {
  await loadHistoryIndex({ silent: true });

  const liveUrl = getLiveReportUrl();
  try {
    await loadFromUrl(liveUrl);
    viewMode.textContent = inferViewMode(liveUrl);
    return;
  } catch (error) {
    if (isNoDataError(error)) {
      clearDashboard("No live data published yet", "Use Refresh Live Data to run a manual collection.");
      sourceStatus.textContent = "No live report is available yet.";
      return;
    }
    sourceStatus.textContent = formatLoadError(liveUrl, error);
  }
}

async function loadFromUrl(url) {
  if (!url) {
    throw new Error("Missing report URL");
  }

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    const error = new Error(payload?.detail || `Failed to load report: HTTP ${response.status}`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  const payload = await response.json();
  ingestTopics(payload);
  void loadDebugSources();
  sourceStatus.textContent = `Loaded ${state.allTopics.length} topics from ${url}`;
  currentSource.textContent = shortenUrl(url);
  viewMode.textContent = inferViewMode(url);
  return payload;
}

async function loadDebugSources() {
  const debugUrl = `${DEFAULT_REMOTE_BASE}/debug-sources`;
  try {
    const response = await fetch(debugUrl, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    console.group("Trend Play Radar Debug Sources");
    console.log("published_at:", payload.published_at);
    console.log("signal_count:", payload.signal_count);
    Object.entries(payload.platforms || {}).forEach(([platform, info]) => {
      console.group(platform);
      console.log("count:", info.count);
      console.log("samples:", info.samples || []);
      console.groupEnd();
    });
    console.groupEnd();
  } catch (error) {
    console.warn("Trend Play Radar debug source fetch failed:", error);
  }
}

function formatLoadError(url, error) {
  const message = error instanceof Error ? error.message : String(error || "Unknown error");
  return `Failed to load ${shortenUrl(url)}: ${message}`;
}

function formatRefreshError(error) {
  const message = error instanceof Error ? error.message : String(error || "Unknown error");
  return `Refresh failed: ${message}`;
}

async function loadHistoryIndex({ silent = false } = {}) {
  const url = buildHistoryIndexUrl();
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to load history index: HTTP ${response.status}`);
    }
    historyEntries = await response.json();
    populateHistorySelect(url);
    try {
      localStorage.setItem(historyStorageKey, url);
    } catch {
      // Ignore storage failures.
    }
    if (!silent) {
      sourceStatus.textContent = `Loaded ${historyEntries.length} history batches from ${url}`;
    }
  } catch {
    historyEntries = [];
    populateHistorySelect(url);
    if (!silent) {
      sourceStatus.textContent = `History index unavailable from ${url}`;
    }
  }
}

function ingestTopics(payload) {
  state.allTopics = Array.isArray(payload) ? payload : payload?.topics || payload?.records || [];
  lastPublished.textContent = payload?.published_at ? formatTimestamp(payload.published_at) : "n/a";
  populatePlatformFilter();
  applyFilters();
  renderSourceComparison();
}

function clearDashboard(title, detail) {
  state.allTopics = [];
  state.filteredTopics = [];
  topicList.innerHTML = "";
  sourceComparison.innerHTML = "";
  topicCount.textContent = "0";
  highConfidenceCount.textContent = "0";
  averagePriority.textContent = "0";
  lastPublished.textContent = "n/a";
  currentSource.textContent = "n/a";
  if (emptyTitle) emptyTitle.textContent = title;
  if (emptyDetail) emptyDetail.textContent = detail;
  emptyState.classList.remove("hidden");
}

function populatePlatformFilter() {
  const platforms = new Set();
  for (const topic of state.allTopics) {
    for (const platform of topic.platforms || []) {
      platforms.add(platform);
    }
  }

  const current = platformFilter.value;
  platformFilter.innerHTML = '<option value="all">All</option>';
  Array.from(platforms)
    .sort()
    .forEach((platform) => {
      const option = document.createElement("option");
      option.value = platform;
      option.textContent = platform;
      platformFilter.appendChild(option);
    });
  platformFilter.value = Array.from(platforms).includes(current) ? current : "all";
}

function populateHistorySelect(indexUrl) {
  historySelect.innerHTML = '<option value="">Select a saved batch</option>';
  historyEntries.forEach((entry) => {
    const option = document.createElement("option");
    option.value = resolveHistoryJsonUrl(entry.json_path, indexUrl);
    option.textContent = `${entry.batch_id} · ${entry.topic_count} topics · ${formatTimestamp(entry.published_at)}`;
    historySelect.appendChild(option);
  });
  historyCount.textContent = String(historyEntries.length);
}

function applyFilters() {
  const classification = classificationFilter.value;
  const platform = platformFilter.value;
  const search = searchFilter.value.trim().toLowerCase();

  state.filteredTopics = state.allTopics.filter((topic) => {
    const matchesClassification = classification === "all" || topic.classification === classification;
    const matchesPlatform = platform === "all" || (topic.platforms || []).includes(platform);
    const haystack = [
      topic.label,
      ...(topic.keywords || []),
      ...(topic.suggested_game_formats || []),
      ...(topic.suggested_marketing_hooks || []),
    ]
      .join(" ")
      .toLowerCase();
    const matchesSearch = !search || haystack.includes(search);
    return matchesClassification && matchesPlatform && matchesSearch;
  });

  renderSummary();
  renderTopics();
}

function renderSummary() {
  topicCount.textContent = String(state.filteredTopics.length);
  highConfidenceCount.textContent = String(
    state.filteredTopics.filter((topic) => topic.classification === "high-confidence candidate").length
  );

  const average =
    state.filteredTopics.length === 0
      ? 0
      : state.filteredTopics.reduce((sum, topic) => sum + Number(topic.final_priority_score || 0), 0) /
        state.filteredTopics.length;
  averagePriority.textContent = average.toFixed(1);
}

function renderTopics() {
  topicList.innerHTML = "";
  const topics = state.filteredTopics;

  if (topics.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");

  topics.forEach((topic, index) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".topic-rank").textContent = `Rank #${index + 1}`;
    node.querySelector(".topic-label").textContent = topic.label;

    const pill = node.querySelector(".classification-pill");
    pill.textContent = topic.classification;
    pill.classList.add(classificationClass(topic.classification));

    node.querySelector(".priority-score").textContent = formatScore(topic.final_priority_score);
    node.querySelector(".confidence-score").textContent = formatScore(topic.confidence_score);
    node.querySelector(".execution-score").textContent = formatScore(topic.execution_fit_score);
    node.querySelector(".spike-risk").textContent = topic.spike_risk;
    node.querySelector(".trend-direction").textContent = formatTrendDirection(topic.trend_direction);
    node.querySelector(".trend-summary").textContent = topic.trend_summary || "No trend explanation yet.";
    renderTrendChart(
      node.querySelector(".trend-chart"),
      node.querySelector(".trend-chart-labels"),
      topic.trend_series || []
    );

    fillTagRow(node.querySelector(".platforms"), topic.platforms || []);
    fillTagRow(node.querySelector(".keywords"), topic.keywords || []);
    fillList(node.querySelector(".format-list"), topic.suggested_game_formats || []);
    fillList(node.querySelector(".hook-list"), topic.suggested_marketing_hooks || []);
    fillList(node.querySelector(".evidence-list"), topic.evidence || []);
    fillList(node.querySelector(".notes-list"), topic.notes || []);
    fillList(node.querySelector(".signals-list"), topic.signal_ids || []);

    topicList.appendChild(node);
  });
}

function renderSourceComparison() {
  sourceComparison.innerHTML = "";

  const platformGroups = new Map();
  for (const topic of state.allTopics) {
    for (const platform of topic.platforms || []) {
      const current = platformGroups.get(platform) || [];
      current.push(topic);
      platformGroups.set(platform, current);
    }
  }

  const preferredOrder = ["youtube", "google_trends", "rss"];
  const orderedPlatforms = Array.from(new Set([...preferredOrder, ...platformGroups.keys()])).filter((platform) =>
    platformGroups.has(platform)
  );

  if (!orderedPlatforms.length) {
    sourceComparison.innerHTML = '<div class="source-card"><h4>No source comparison yet</h4></div>';
    return;
  }

  orderedPlatforms.forEach((platform) => {
    const topics = platformGroups.get(platform) || [];
    const avgPriority = averageOf(topics, "final_priority_score");
    const avgConfidence = averageOf(topics, "confidence_score");
    const avgExecution = averageOf(topics, "execution_fit_score");
    const highConfidence = topics.filter((topic) => topic.classification === "high-confidence candidate").length;

    const card = document.createElement("article");
    card.className = "source-card";
    card.innerHTML = `
      <h4>${formatPlatformName(platform)}</h4>
      <div class="source-grid">
        <div class="source-stat">
          <span>Topics</span>
          <strong>${topics.length}</strong>
        </div>
        <div class="source-stat">
          <span>High Confidence</span>
          <strong>${highConfidence}</strong>
        </div>
        <div class="source-stat">
          <span>Avg Priority</span>
          <strong>${avgPriority.toFixed(1)}</strong>
        </div>
        <div class="source-stat">
          <span>Avg Confidence</span>
          <strong>${avgConfidence.toFixed(1)}</strong>
        </div>
        <div class="source-stat">
          <span>Avg Execution</span>
          <strong>${avgExecution.toFixed(1)}</strong>
        </div>
        <div class="source-stat">
          <span>Role</span>
          <strong>${
            platform === "youtube"
              ? "Broad Attention"
              : platform === "google_trends"
                ? "Validation"
                : platform === "rss"
                  ? "Discovery"
                  : "Signal"
          }</strong>
        </div>
      </div>
    `;
    sourceComparison.appendChild(card);
  });
}

function fillTagRow(container, items) {
  container.innerHTML = "";
  items.forEach((item) => {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = item;
    container.appendChild(span);
  });
}

function fillList(container, items) {
  container.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.textContent = "n/a";
    container.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  });
}

function formatScore(value) {
  return Number(value || 0).toFixed(1);
}

function averageOf(items, key) {
  if (!items.length) return 0;
  return items.reduce((sum, item) => sum + Number(item[key] || 0), 0) / items.length;
}

function formatPlatformName(platform) {
  if (platform === "youtube") return "YouTube";
  if (platform === "google_trends") return "Google Trends";
  if (platform === "rss") return "itch.io / RSS";
  return platform.replaceAll("_", " ");
}

function renderTrendChart(container, labelsContainer, series) {
  if (!container) return;
  const pointsInput = Array.isArray(series) && series.length ? series : defaultTrendSeries();
  const values = pointsInput.map((point) => Number(point.value || 0));
  const max = Math.max(...values, 1);
  const count = pointsInput.length;
  const step = count > 1 ? 148 / (count - 1) : 0;
  const points = values
    .map((value, index) => {
      const x = 16 + index * step;
      const y = 54 - (value / max) * 40;
      return `${x},${y}`;
    })
    .join(" ");

  container.innerHTML = `
    <polyline fill="none" stroke="rgba(13, 92, 99, 0.28)" stroke-width="10" stroke-linecap="round" points="${points}"></polyline>
    <polyline fill="none" stroke="#0d5c63" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${points}"></polyline>
    ${values
      .map((value, index) => {
        const x = 16 + index * step;
        const y = 54 - (value / max) * 40;
        return `<circle cx="${x}" cy="${y}" r="4.5" fill="#fffdf8" stroke="#0d5c63" stroke-width="2"></circle>
          <text x="${x}" y="${Math.max(y - 8, 10)}" text-anchor="middle" font-size="10" fill="#6a5f51">${formatCompact(
            value
          )}</text>`;
      })
      .join("")}
  `;

  if (labelsContainer) {
    labelsContainer.innerHTML = pointsInput
      .map((point) => `<span>${point.label || ""}</span>`)
      .join("");
  }
}

function formatCompact(value) {
  const numeric = Number(value || 0);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}

function defaultTrendSeries() {
  return [
    { label: "n/a", value: 0 },
    { label: "n/a", value: 0 },
    { label: "n/a", value: 0 },
  ];
}

function formatTrendDirection(value) {
  if (value === "spiking") return "Spiking";
  if (value === "rising") return "Rising";
  if (value === "cooling") return "Cooling";
  if (value === "steady") return "Steady";
  if (value === "weak") return "Weak";
  return "Thin Signal";
}

function classificationClass(value) {
  if (value === "high-confidence candidate") return "high-confidence";
  if (value === "watchlist candidate") return "watchlist";
  return "noisy";
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function getLiveReportUrl() {
  return `${DEFAULT_REMOTE_BASE}/report`;
}

function buildHistoryIndexUrl() {
  try {
    const saved = localStorage.getItem(historyStorageKey);
    if (saved) return saved;
  } catch {
    // Ignore storage failures.
  }

  return `${DEFAULT_REMOTE_BASE}/history-index`;
}

function resolveHistoryJsonUrl(relativePath, indexUrl) {
  try {
    const base = new URL(indexUrl, window.location.href);
    if (base.pathname.endsWith("/history-index")) {
      if (relativePath.startsWith("/")) {
        return new URL(relativePath, `${base.origin}/`).toString();
      }
      const path = relativePath.includes("history/") ? relativePath : `history/${relativePath}`;
      return new URL(path.replace(/^\/+/, ""), `${base.origin}/`).toString();
    }
    return new URL(relativePath, base).toString();
  } catch {
    return relativePath;
  }
}

function inferViewMode(url) {
  if (url.includes("/history/")) return "history";
  if (url.includes("/report")) return "live";
  return "latest";
}

async function triggerRefresh() {
  const response = await fetch(`${DEFAULT_REMOTE_BASE}/refresh`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: "{}",
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const error = new Error(payload?.detail || `Refresh failed: HTTP ${response.status}`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

function buildRefreshSummary(payload) {
  const topicCountValue = payload?.topic_count ?? 0;
  const signalCount = payload?.signal_count ?? 0;
  const googleCount = payload?.sources?.google_trends?.count ?? 0;
  const rssCount = payload?.sources?.rss?.count ?? 0;
  return `Refresh completed. ${topicCountValue} topics from ${signalCount} fresh signals. RSS ${rssCount}, Google Trends ${googleCount}.`;
}

function isNoDataError(error) {
  return error && Number(error.status) === 502;
}

function shortenUrl(url) {
  try {
    const parsed = new URL(url, window.location.href);
    return `${parsed.hostname}${parsed.pathname}`;
  } catch {
    return url;
  }
}
