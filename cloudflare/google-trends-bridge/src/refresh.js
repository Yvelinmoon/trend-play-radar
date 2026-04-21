const DEFAULT_ITCH_IO_FEEDS = [
  "https://itch.io/feed/new.xml",
  "https://itch.io/feed/featured.xml",
  "https://itch.io/feed/sales.xml",
  "https://itch.io/games/price-free.xml",
];

const DEFAULT_TRENDS_TOPIC_MAP = [
  {
    topic_key: "brainrot_meme",
    topic_label: "Brainrot Meme",
    queries: [
      "brainrot meme",
      "brainrot quiz",
      "brainrot character test",
      "brainrot personality test",
      "chaotic meme quiz",
    ],
  },
  {
    topic_key: "chaos_identity",
    topic_label: "Chaos Identity",
    queries: [
      "chaos meme",
      "alignment chart",
      "which one are you",
      "tier list meme",
      "alignment chart quiz",
      "which chaos type are you",
    ],
  },
  {
    topic_key: "character_archetype",
    topic_label: "Character Archetype",
    queries: [
      "character archetype",
      "character archetype quiz",
      "which character are you",
      "fandom quiz",
      "team picker",
      "alignment test",
      "character personality quiz",
      "what character type are you",
      "which fandom character are you",
    ],
  },
  {
    topic_key: "cozy_puzzle",
    topic_label: "Cozy Puzzle",
    queries: [
      "cozy game",
      "cozy puzzle game",
      "wholesome game",
      "relaxing puzzle game",
      "cozy mystery game",
      "cozy visual novel",
      "wholesome puzzle game",
    ],
  },
  {
    topic_key: "merge_idle",
    topic_label: "Merge Idle",
    queries: [
      "merge game",
      "idle game",
      "merge idle game",
      "merge puzzle game",
      "idle merge game",
      "incremental merge game",
    ],
  },
];

const STOPWORDS = new Set([
  "the", "a", "an", "is", "are", "to", "of", "for", "with", "into", "these", "this", "that", "back", "your",
  "every", "keep", "has", "was", "rise", "search", "searches", "turning", "creators", "posts", "climbing", "mode",
  "short", "side", "scrolling", "img", "free", "src", "https", "http", "itch", "itchio", "google", "trends",
  "signal", "quot", "windows", "linux", "macos", "html", "other", "game", "games", "play", "yes", "confirms",
  "broadening", "escaping", "latest", "score", "scores", "average", "samples", "interest", "topic", "isolated",
]);

const THEME_GROUPS = {
  "personality-quiz": {
    label: "Personality Quiz",
    keywords: ["personality", "quiz", "identity", "character"],
    tokens: new Set(["office", "coworkers", "manager", "workplace", "quiz", "personality", "identity", "alignment", "chart", "class", "classes", "character", "archetypes", "archetype", "fandom", "picker", "brainrot", "test"]),
  },
  "dating-checklist": {
    label: "Dating Checklist",
    keywords: ["dating", "checklist", "relationship", "scorecard"],
    tokens: new Set(["dating", "situationship", "checklist", "questions", "scorecard", "relationship", "flags", "flag", "red"]),
  },
  "cozy-puzzle": {
    label: "Cozy Puzzle",
    keywords: ["cozy", "puzzle", "wholesome", "relaxing"],
    tokens: new Set(["cozy", "puzzle", "wholesome", "relaxing", "story", "mystery", "novel"]),
  },
  "merge-idle": {
    label: "Merge Idle",
    keywords: ["merge", "idle", "incremental", "builder"],
    tokens: new Set(["merge", "idle", "incremental", "sim", "simulation", "builder"]),
  },
  "management-sim": {
    label: "Management Sim",
    keywords: ["management", "simulation", "builder", "tycoon"],
    tokens: new Set(["management", "manager", "simulation", "sim", "builder", "tycoon", "shop", "station", "business", "colony", "houses", "restaurant"]),
  },
  "arcade-shooter": {
    label: "Arcade Shooter",
    keywords: ["shooter", "arcade", "action", "twin-stick"],
    tokens: new Set(["shooter", "shoot", "bullet", "arcade", "blaster", "blasters", "twin", "stick", "combat", "action"]),
  },
  "precision-platformer": {
    label: "Precision Platformer",
    keywords: ["platformer", "precision", "action", "jump"],
    tokens: new Set(["platformer", "platforming", "precision", "jump", "runner", "metroidvania", "parkour"]),
  },
  "card-strategy": {
    label: "Card Strategy",
    keywords: ["card", "strategy", "deck", "tactics"],
    tokens: new Set(["card", "cards", "deck", "chess", "strategy", "tactics", "tactical", "autobattler", "casino", "poker"]),
  },
  "visual-novel-story": {
    label: "Visual Novel Story",
    keywords: ["visual", "novel", "story", "narrative"],
    tokens: new Set(["visual", "novel", "story", "narrative", "dialogue", "romance"]),
  },
  "horror-exploration": {
    label: "Horror Exploration",
    keywords: ["horror", "exploration", "mystery", "adventure"],
    tokens: new Set(["horror", "exploration", "underworld", "nightmare", "dark", "cave", "dungeon", "haunted", "mystery"]),
  },
  "educational-sim": {
    label: "Educational Sim",
    keywords: ["educational", "simulation", "learning", "management"],
    tokens: new Set(["educational", "education", "learning", "recycle", "recycling", "school", "management"]),
  },
};

const GAME_FORMAT_RULES = {
  quiz: "personality quiz",
  personality: "personality quiz",
  identity: "personality quiz",
  boss: "side-scrolling boss fight",
  fight: "side-scrolling boss fight",
  combat: "side-scrolling boss fight",
  parody: "timed reaction challenge",
  routine: "timed reaction challenge",
  character: "class sorter",
  office: "class sorter",
  dating: "scorecard test",
  checklist: "scorecard test",
};

const HOOK_RULES = {
  quiz: "Find out which role you really are",
  personality: "Share your result card before your friends do",
  boss: "Beat the boss everyone knows from real life",
  fight: "Can you survive the final phase",
  office: "Every team has one. Which one are you",
  routine: "Rate how cursed your daily loop has become",
  dating: "See how many red flags your result unlocks",
  checklist: "Turn private panic into a shareable scorecard",
};

const GOOGLE_TRENDS_ROOT = "https://trends.google.com/trends/api";
const CURRENT_WINDOW_MS = 24 * 60 * 60 * 1000;
const PREVIOUS_WINDOW_MS = 24 * 60 * 60 * 1000;
const BASELINE_DAYS = 7;
const HISTORY_RETENTION_MS = 14 * 24 * 60 * 60 * 1000;

export async function runManualRefresh(existingSignals = []) {
  const nowIso = new Date().toISOString();
  const rssResult = await fetchRssSignals();
  const googleResult = await fetchGoogleTrendsSignals();
  const freshSignals = [...rssResult.signals, ...googleResult.signals];
  const signalHistory = mergeSignalHistory(existingSignals, freshSignals);
  const topics = scoreTopics(clusterSignals(signalHistory));

  return {
    bridgePayload: {
      cached_at: nowIso,
      records: googleResult.records,
    },
    reportPayload: {
      published_at: nowIso,
      batch_id: buildBatchId(nowIso),
      topics,
    },
    debugPayload: buildDebugSourcesPayload(nowIso, freshSignals, {
      rss: rssResult.meta,
      google_trends: googleResult.meta,
    }),
    signalHistory,
    refreshSummary: {
      published_at: nowIso,
      topic_count: topics.length,
      signal_count: freshSignals.length,
      history_signal_count: signalHistory.length,
      sources: {
        rss: rssResult.meta,
        google_trends: googleResult.meta,
      },
    },
  };
}

function mergeSignalHistory(existingSignals, freshSignals) {
  const now = Date.now();
  const minTime = now - HISTORY_RETENTION_MS;
  const merged = new Map();
  for (const signal of [...existingSignals, ...freshSignals]) {
    const publishedAt = new Date(signal.published_at).getTime();
    if (!Number.isFinite(publishedAt) || publishedAt < minTime) continue;
    const current = merged.get(signal.external_id);
    if (!current || publishedAt > new Date(current.published_at).getTime()) {
      merged.set(signal.external_id, signal);
    }
  }
  return Array.from(merged.values()).sort((a, b) => new Date(a.published_at) - new Date(b.published_at));
}

async function fetchRssSignals() {
  const signals = [];
  const errors = [];
  for (const feed of DEFAULT_ITCH_IO_FEEDS) {
    try {
      const response = await fetch(feed, { cf: { cacheTtl: 300, cacheEverything: true } });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const xml = await response.text();
      signals.push(...parseRssFeed(xml, feed));
    } catch (error) {
      errors.push({ feed, error: error.message || String(error) });
    }
  }
  return {
    signals,
    meta: {
      status: errors.length && !signals.length ? "error" : "ok",
      count: signals.length,
      feeds: DEFAULT_ITCH_IO_FEEDS,
      errors,
    },
  };
}

function parseRssFeed(xml, source) {
  const items = extractBlocks(xml, "item");
  const entries = items.length ? items : extractBlocks(xml, "entry");
  return entries.map((block, index) => parseFeedItem(block, source, index)).filter(Boolean);
}

function parseFeedItem(block, source, index) {
  const rawTitle = firstMatch(block, /<title[^>]*><!\[CDATA\[(.*?)\]\]><\/title>|<title[^>]*>(.*?)<\/title>/is);
  const title = cleanTitle(rawTitle);
  const url =
    firstMatch(block, /<link[^>]*href=["']([^"']+)["'][^>]*\/?>/i) ||
    firstMatch(block, /<link[^>]*>(.*?)<\/link>/is);
  const publishedAtRaw =
    firstMatch(block, /<pubDate[^>]*>(.*?)<\/pubDate>/is) ||
    firstMatch(block, /<published[^>]*>(.*?)<\/published>/is) ||
    firstMatch(block, /<updated[^>]*>(.*?)<\/updated>/is);
  const summary =
    decodeHtmlEntities(
      stripHtml(
        firstMatch(block, /<description[^>]*><!\[CDATA\[(.*?)\]\]><\/description>|<description[^>]*>(.*?)<\/description>/is) ||
          firstMatch(block, /<summary[^>]*><!\[CDATA\[(.*?)\]\]><\/summary>|<summary[^>]*>(.*?)<\/summary>/is) ||
          ""
      )
    ).trim();
  const categories = Array.from(block.matchAll(/<category[^>]*>(.*?)<\/category>|<category[^>]*term=["']([^"']+)["'][^>]*\/?>/gis))
    .map((match) => decodeHtmlEntities((match[1] || match[2] || "").trim().toLowerCase()))
    .filter(Boolean);
  const platformTags = [];
  const rawTitleLower = (rawTitle || "").toLowerCase();
  if (rawTitleLower.includes("[html")) platformTags.push("html");
  if (rawTitleLower.includes("[windows")) platformTags.push("windows");
  if (rawTitleLower.includes("[mac")) platformTags.push("osx");
  if (rawTitleLower.includes("[linux")) platformTags.push("linux");

  const publishedAt = parseDateSafe(publishedAtRaw);
  const idSeed = `${source}|${url || ""}|${title || ""}|${publishedAt || index}`;
  return {
    platform: "rss",
    external_id: `rss-${hashString(idSeed)}`,
    title: title || "Untitled RSS item",
    url: url || source,
    published_at: publishedAt || new Date().toISOString(),
    engagement: 0,
    summary,
    tags: categories,
    metrics: {},
    author: "",
    keyword_hint: [title, ...categories, summary].filter(Boolean).join(" "),
    raw_payload: {
      source,
      source_name: "itch.io RSS",
      raw_title: decodeHtmlEntities((rawTitle || "").trim()),
      plain_title: title || "Untitled RSS item",
      platform_tags: platformTags,
    },
  };
}

async function fetchGoogleTrendsSignals() {
  const records = [];
  const errors = [];
  for (const batch of batched(buildTrendQueries(DEFAULT_TRENDS_TOPIC_MAP), 5)) {
    try {
      const widget = await fetchTimeseriesWidget(batch.map((item) => item.query));
      records.push(...(await fetchKeywordRecords(widget, batch)));
    } catch (error) {
      errors.push({ queries: batch.map((item) => item.query), error: error.message || String(error) });
    }
  }
  return {
    records,
    signals: records.map((record) => ({
      platform: "google_trends",
      external_id: record.external_id,
      title: record.title,
      url: record.url,
      published_at: record.published_at,
      engagement: Number(record.trend_score || 0),
      summary: record.summary || "",
      tags: Array.isArray(record.tags) ? record.tags : [],
      metrics: { trend_score: Number(record.trend_score || 0) },
      author: "",
      keyword_hint: [record.topic_label || "", record.query || "", record.keyword || ""].filter(Boolean).join(" "),
      raw_payload: record.raw_payload || {},
    })),
    meta: {
      status: errors.length && !records.length ? "error" : "ok",
      count: records.length,
      errors,
    },
  };
}

function buildTrendQueries(topicMap) {
  return topicMap.flatMap((topic) =>
    topic.queries.map((query) => ({
      topic_key: topic.topic_key,
      topic_label: topic.topic_label,
      query,
      tags: tokenize(`${topic.topic_label} ${query}`).slice(0, 4),
    }))
  );
}

async function fetchTimeseriesWidget(keywords) {
  const req = {
    comparisonItem: keywords.map((keyword) => ({ keyword, geo: "US", time: "now 7-d" })),
    category: 0,
    property: "",
  };
  const payload = await trendsApiRequest("explore", { req: JSON.stringify(req) });
  const widget = (payload.widgets || []).find((item) => item.id === "TIMESERIES");
  if (!widget) {
    throw new Error("Google Trends explore response did not include a TIMESERIES widget");
  }
  return widget;
}

async function fetchKeywordRecords(widget, queries) {
  const payload = await trendsApiRequest("widgetdata/multiline", {
    req: JSON.stringify(widget.request),
    token: widget.token,
  });
  const timeline = payload.default?.timelineData || [];
  const nowIso = new Date().toISOString();
  return queries.map((trendQuery, index) => {
    const series = extractSeries(timeline, index);
    const latestScore = series.length ? series[series.length - 1].value : 0;
    const peakScore = Math.max(0, ...series.map((point) => point.value));
    const averageScore = series.length ? round(series.reduce((sum, point) => sum + point.value, 0) / series.length, 2) : 0;
    return {
      external_id: `gt-${slugify(trendQuery.query)}-${nowIso.slice(0, 10)}`,
      keyword: trendQuery.query,
      query: trendQuery.query,
      parent_topic: trendQuery.topic_key,
      topic_label: trendQuery.topic_label,
      title: `Google Trends signal for ${trendQuery.query}`,
      url: buildExploreUrl(trendQuery.query),
      published_at: nowIso,
      trend_score: latestScore,
      tags: trendQuery.tags,
      summary: `Latest score ${latestScore}, peak score ${peakScore}, average score ${averageScore} over ${series.length} samples.`,
      raw_payload: {
        topic_key: trendQuery.topic_key,
        topic_label: trendQuery.topic_label,
        query: trendQuery.query,
        geo: "US",
        series,
        peak_score: peakScore,
        average_score: averageScore,
      },
    };
  }).filter((record) => record.trend_score > 0);
}

async function trendsApiRequest(path, params) {
  const url = new URL(`${GOOGLE_TRENDS_ROOT}/${path}`);
  url.searchParams.set("hl", "en-US");
  url.searchParams.set("tz", "0");
  Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
  const response = await fetch(url.toString(), {
    headers: {
      accept: "application/json,text/plain,*/*",
      "accept-language": "en-US,en;q=0.9",
    },
    cf: { cacheTtl: 0 },
  });
  if (!response.ok) {
    throw new Error(`Google Trends HTTP ${response.status}`);
  }
  const raw = await response.text();
  return JSON.parse(raw.replace(/^\)\]\}',?\s*/, ""));
}

function extractSeries(timeline, keywordIndex) {
  return timeline
    .map((point) => {
      const values = Array.isArray(point.value) ? point.value : [];
      if (keywordIndex >= values.length) return null;
      return {
        time: point.time,
        formatted_time: point.formattedTime || "",
        value: Number(values[keywordIndex] || 0),
      };
    })
    .filter(Boolean);
}

function buildExploreUrl(keyword) {
  const url = new URL("https://trends.google.com/trends/explore");
  url.searchParams.set("q", keyword);
  url.searchParams.set("geo", "US");
  url.searchParams.set("date", "now 7-d");
  return url.toString();
}

function buildDebugSourcesPayload(publishedAt, signals, sourceMeta) {
  const grouped = {};
  for (const signal of signals) {
    const bucket = grouped[signal.platform] || [];
    bucket.push(signal);
    grouped[signal.platform] = bucket;
  }
  const platforms = {};
  for (const [platform, items] of Object.entries(grouped)) {
    const samples = [...items]
      .sort((a, b) => new Date(b.published_at) - new Date(a.published_at))
      .slice(0, 5)
      .map((signal) => ({
        external_id: signal.external_id,
        title: signal.title,
        url: signal.url,
        published_at: signal.published_at,
        engagement: signal.engagement,
        summary: signal.summary,
        tags: signal.tags,
        keyword_hint: signal.keyword_hint,
        raw_payload: signal.raw_payload,
      }));
    platforms[platform] = {
      count: items.length,
      status: sourceMeta[platform]?.status || "ok",
      errors: sourceMeta[platform]?.errors || [],
      samples,
    };
  }
  for (const platform of ["rss", "google_trends"]) {
    if (!platforms[platform]) {
      platforms[platform] = {
        count: 0,
        status: sourceMeta[platform]?.status || "ok",
        errors: sourceMeta[platform]?.errors || [],
        samples: [],
      };
    }
  }
  return {
    published_at: publishedAt,
    signal_count: signals.length,
    platforms,
  };
}

function clusterSignals(signals) {
  const buckets = new Map();
  for (const signal of signals) {
    const key = deriveTopicKey(signal);
    const current = buckets.get(key) || [];
    current.push(signal);
    buckets.set(key, current);
  }
  return buckets;
}

function deriveTopicKey(signal) {
  const candidates = [signal.keyword_hint, signal.title, signal.summary, ...(signal.tags || [])].join(" ");
  const tokens = tokenize(candidates);
  if (!tokens.length) return `${signal.platform}:${signal.external_id}`;
  const thematicKey = deriveThemeKey(tokens);
  if (thematicKey) return thematicKey;
  return [...tokens]
    .sort((left, right) => scoreToken(right) - scoreToken(left) || left.localeCompare(right))
    .slice(0, 3)
    .join("-");
}

function tokenize(value) {
  return (String(value || "").toLowerCase().match(/[a-z0-9]+/g) || []).filter(
    (token) => token.length > 2 && !STOPWORDS.has(token)
  );
}

function deriveThemeKey(tokens) {
  const tokenSet = new Set(tokens);
  let bestMatch = null;
  for (const [themeKey, metadata] of Object.entries(THEME_GROUPS)) {
    const themeTokens = metadata.tokens;
    let overlap = 0;
    for (const token of tokenSet) {
      if (themeTokens.has(token)) overlap += 1;
    }
    if (overlap < 2) continue;
    if (!bestMatch || overlap > bestMatch.overlap || (overlap === bestMatch.overlap && themeTokens.size < bestMatch.tokenCount)) {
      bestMatch = { themeKey, overlap, tokenCount: themeTokens.size };
    }
  }
  return bestMatch?.themeKey || null;
}

function topicLabelForKey(topicKey) {
  return THEME_GROUPS[topicKey]?.label || "";
}

function topicKeywordsForKey(topicKey) {
  return [...(THEME_GROUPS[topicKey]?.keywords || [])];
}

function scoreToken(token) {
  return Math.log(token.length + 1);
}

function scoreTopics(clusteredSignals) {
  return Array.from(clusteredSignals.entries())
    .map(([topicKey, signals]) => buildTopic(topicKey, signals))
    .sort((left, right) => right.final_priority_score - left.final_priority_score);
}

function buildTopic(topicKey, signals) {
  const referenceTime = signals.reduce((latest, signal) => {
    const time = new Date(signal.published_at).getTime();
    return Math.max(latest, time);
  }, Date.now());
  const keywords = extractKeywords(signals, topicKey);
  const platformCounts = countPlatforms(signals);
  const windows = splitWindows(signals, referenceTime);
  const currentEngagement = sum(windows.current.map((signal) => signal.engagement || 0));
  const previousEngagement = sum(windows.previous.map((signal) => signal.engagement || 0));
  const baselineAverage = computeBaselineAverage(windows.baseline, referenceTime);
  const baselineEngagement = computeEngagementBaseline(windows.baseline, referenceTime);
  const growthRatio = computeGrowthRatio(windows.current.length, windows.previous.length, baselineAverage);
  const engagementGrowthRatio = computeGrowthRatio(currentEngagement, previousEngagement, baselineEngagement);
  const burstScore = scoreBurst(windows.current.length, baselineAverage);
  const growthScore = scoreGrowth(growthRatio, engagementGrowthRatio);
  const spreadScore = scoreSpread(platformCounts);
  const confirmationScore = scoreConfirmation(signals, platformCounts);
  const confidenceScore = round(Math.min(burstScore + growthScore + spreadScore + confirmationScore, 100), 1);
  const gameFitScore = round(scoreGameFit(keywords), 1);
  const marketingFitScore = round(scoreMarketingFit(keywords), 1);
  const productionFeasibilityScore = round(scoreProductionFeasibility(keywords), 1);
  const contentQualityScore = round(scoreContentQuality(signals, keywords), 1);
  const executionFitScore = round(
    Math.min(gameFitScore + marketingFitScore + productionFeasibilityScore + contentQualityScore, 100),
    1
  );
  const finalPriorityScore = round(confidenceScore * 0.6 + executionFitScore * 0.4, 1);
  const hasSearchConfirmation = Object.prototype.hasOwnProperty.call(platformCounts, "google_trends");
  const spikeRisk = assessSpikeRisk({
    currentWindowCount: windows.current.length,
    previousWindowCount: windows.previous.length,
    platformCounts,
    hasSearchConfirmation,
  });
  const classification = classifyTopic({
    confidenceScore,
    executionFitScore,
    spikeRisk,
    hasSearchConfirmation,
  });
  const trendSeries = buildTrendSeries(signals, referenceTime);
  const trendDirection = assessTrendDirection(trendSeries);
  const trendSummary = buildTrendSummary({
    trendSeries,
    trendDirection,
    currentWindowCount: windows.current.length,
    previousWindowCount: windows.previous.length,
    hasSearchConfirmation,
  });
  const suggestedGameFormats = suggestGameFormats(keywords);
  const suggestedMarketingHooks = suggestMarketingHooks(keywords);

  return {
    topic_key: topicKey,
    label: buildLabel(topicKey, keywords),
    platforms: Object.keys(platformCounts).sort(),
    keywords,
    current_window_count: windows.current.length,
    previous_window_count: windows.previous.length,
    baseline_window_average: round(baselineAverage, 2),
    current_engagement: round(currentEngagement, 1),
    previous_engagement: round(previousEngagement, 1),
    growth_ratio: round(growthRatio, 2),
    engagement_growth_ratio: round(engagementGrowthRatio, 2),
    burst_score: round(burstScore, 1),
    growth_score: round(growthScore, 1),
    spread_score: round(spreadScore, 1),
    confirmation_score: round(confirmationScore, 1),
    confidence_score: confidenceScore,
    game_fit_score: gameFitScore,
    marketing_fit_score: marketingFitScore,
    production_feasibility_score: productionFeasibilityScore,
    execution_fit_score: executionFitScore,
    final_priority_score: finalPriorityScore,
    classification,
    spike_risk: spikeRisk,
    trend_direction: trendDirection,
    trend_summary: trendSummary,
    trend_series: trendSeries,
    suggested_game_formats: suggestedGameFormats,
    suggested_marketing_hooks: suggestedMarketingHooks,
    notes: buildNotes({
      currentWindowCount: windows.current.length,
      previousWindowCount: windows.previous.length,
      baselineWindowAverage: baselineAverage,
      growthRatio,
      confidenceScore,
      executionFitScore,
      classification,
      spikeRisk,
    }),
    evidence: buildEvidence({
      signals,
      platformCounts,
      currentWindowCount: windows.current.length,
      previousWindowCount: windows.previous.length,
      baselineWindowAverage: baselineAverage,
      currentEngagement,
      previousEngagement,
      growthRatio,
      engagementGrowthRatio,
    }),
    signal_count: signals.length,
    signal_ids: signals.map((signal) => signal.external_id),
  };
}

function countPlatforms(signals) {
  return signals.reduce((counts, signal) => {
    counts[signal.platform] = (counts[signal.platform] || 0) + 1;
    return counts;
  }, {});
}

function splitWindows(signals, referenceTime) {
  const currentStart = referenceTime - CURRENT_WINDOW_MS;
  const previousStart = currentStart - PREVIOUS_WINDOW_MS;
  const baselineStart = previousStart - BASELINE_DAYS * CURRENT_WINDOW_MS;
  return {
    current: signals.filter((signal) => {
      const time = new Date(signal.published_at).getTime();
      return time >= currentStart && time <= referenceTime;
    }),
    previous: signals.filter((signal) => {
      const time = new Date(signal.published_at).getTime();
      return time >= previousStart && time < currentStart;
    }),
    baseline: signals.filter((signal) => {
      const time = new Date(signal.published_at).getTime();
      return time >= baselineStart && time < previousStart;
    }),
  };
}

function computeBaselineAverage(signals, referenceTime) {
  if (!signals.length) return 0;
  const buckets = Array.from({ length: BASELINE_DAYS }, () => 0);
  const baselineStart = referenceTime - CURRENT_WINDOW_MS - PREVIOUS_WINDOW_MS - BASELINE_DAYS * CURRENT_WINDOW_MS;
  for (const signal of signals) {
    const offset = new Date(signal.published_at).getTime() - baselineStart;
    const index = Math.floor(offset / CURRENT_WINDOW_MS);
    if (index >= 0 && index < BASELINE_DAYS) buckets[index] += 1;
  }
  const nonEmpty = buckets.filter((value) => value > 0);
  return nonEmpty.length ? sum(nonEmpty) / nonEmpty.length : 0;
}

function computeEngagementBaseline(signals, referenceTime) {
  if (!signals.length) return 0;
  const buckets = Array.from({ length: BASELINE_DAYS }, () => 0);
  const baselineStart = referenceTime - CURRENT_WINDOW_MS - PREVIOUS_WINDOW_MS - BASELINE_DAYS * CURRENT_WINDOW_MS;
  for (const signal of signals) {
    const offset = new Date(signal.published_at).getTime() - baselineStart;
    const index = Math.floor(offset / CURRENT_WINDOW_MS);
    if (index >= 0 && index < BASELINE_DAYS) buckets[index] += Number(signal.engagement || 0);
  }
  const nonEmpty = buckets.filter((value) => value > 0);
  return nonEmpty.length ? sum(nonEmpty) / nonEmpty.length : 0;
}

function computeGrowthRatio(current, previous, baseline) {
  return current / Math.max(previous, baseline, 1);
}

function scoreBurst(currentWindowCount, baselineWindowAverage) {
  if (!currentWindowCount) return 0;
  const burstRatio = currentWindowCount / Math.max(baselineWindowAverage, 1);
  return Math.min(Math.ceil(burstRatio * 8), 20);
}

function scoreGrowth(growthRatio, engagementGrowthRatio) {
  let score = 0;
  if (growthRatio >= 1.2) score += Math.min((growthRatio - 1) * 12, 14);
  if (engagementGrowthRatio >= 1.1) score += Math.min((engagementGrowthRatio - 1) * 4, 6);
  return Math.min(score, 20);
}

function scoreSpread(platformCounts) {
  let score = Math.min(Object.keys(platformCounts).length * 6, 18);
  if (platformCounts.reddit && platformCounts.google_trends) score += 4;
  return Math.min(score, 22);
}

function scoreConfirmation(signals, platformCounts) {
  let score = 0;
  if (platformCounts.google_trends) score += 8;
  if (signals.length >= 3) score += 3;
  if (uniqueAuthors(signals) >= 2) score += 2;
  return Math.min(score, 15);
}

function scoreGameFit(keywords) {
  let total = 0;
  for (const keyword of keywords) {
    if (["quiz", "personality", "identity", "boss", "fight", "character", "office"].includes(keyword)) total += 7;
    else if (["parody", "routine", "meme", "shareable", "dating", "checklist"].includes(keyword)) total += 5;
    else total += 1.5;
  }
  return Math.min(total, 35);
}

function scoreMarketingFit(keywords) {
  let total = 0;
  for (const keyword of keywords) {
    if (["meme", "identity", "office", "boss", "dating"].includes(keyword)) total += 5;
    else if (["character", "parody", "quiz", "checklist"].includes(keyword)) total += 3.5;
    else total += 1;
  }
  return Math.min(total, 25);
}

function scoreProductionFeasibility(keywords) {
  const fastFormats = new Set(["quiz", "personality", "identity", "office", "character", "routine", "dating", "checklist"]);
  const heavierFormats = new Set(["combat", "boss", "fight"]);
  if (keywords.some((keyword) => fastFormats.has(keyword))) return 20;
  if (keywords.some((keyword) => heavierFormats.has(keyword))) return 14;
  return 12;
}

function scoreContentQuality(signals, keywords) {
  const titleLengths = signals.map((signal) => String(signal.title || "").split(/\s+/).filter(Boolean).length);
  const meaningfulSummaries = signals.filter((signal) => String(signal.summary || "").trim().length >= 24);
  const genreKeywords = new Set(["puzzle", "cozy", "merge", "idle", "wholesome", "visual", "novel", "adventure", "simulation", "sports", "action", "platformer", "metroidvania", "survival", "management", "educational", "shooter"]);
  let score = 0;
  if (meaningfulSummaries.length) score += 4;
  if (titleLengths.some((length) => length >= 2)) score += 2;
  if (keywords.some((keyword) => genreKeywords.has(keyword))) score += 4;
  return Math.min(score, 10);
}

function classifyTopic({ confidenceScore, executionFitScore, spikeRisk, hasSearchConfirmation }) {
  if (confidenceScore >= 48 && executionFitScore >= 42 && (hasSearchConfirmation || spikeRisk === "low")) {
    return "high-confidence candidate";
  }
  if (confidenceScore >= 30 && executionFitScore >= 32) {
    return "watchlist candidate";
  }
  return "low-confidence or noisy";
}

function assessSpikeRisk({ currentWindowCount, previousWindowCount, platformCounts, hasSearchConfirmation }) {
  if (currentWindowCount >= 3 && previousWindowCount === 0 && Object.keys(platformCounts).length === 1) return "high";
  if (currentWindowCount >= 2 && !hasSearchConfirmation) return "medium";
  return "low";
}

function extractKeywords(signals, topicKey = "") {
  const counts = new Map();
  for (const keyword of topicKeywordsForKey(topicKey)) {
    counts.set(keyword, (counts.get(keyword) || 0) + 3);
  }
  const priorityTokens = new Set(["quiz", "personality", "fandom", "character", "cozy", "puzzle", "merge", "idle", "wholesome", "visual", "novel", "adventure", "simulation", "sports", "action"]);
  for (const signal of signals) {
    for (const token of tokenize([signal.keyword_hint, signal.title, signal.summary, ...(signal.tags || [])].join(" "))) {
      counts.set(token, (counts.get(token) || 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .sort((left, right) => {
      const leftPriority = priorityTokens.has(left[0]) ? 0 : 1;
      const rightPriority = priorityTokens.has(right[0]) ? 0 : 1;
      return leftPriority - rightPriority || right[1] - left[1] || right[0].length - left[0].length || left[0].localeCompare(right[0]);
    })
    .slice(0, 6)
    .map(([token]) => token);
}

function buildTrendSeries(signals, referenceTime) {
  const googleSeries = buildGoogleTrendsSeries(signals);
  if (googleSeries.length) return googleSeries;
  return buildSignalCountSeries(signals, referenceTime);
}

function buildGoogleTrendsSeries(signals) {
  const pool = [];
  for (const signal of signals) {
    const series = signal.raw_payload?.series || signal.raw_payload?.raw_payload?.series;
    if (Array.isArray(series) && series.length) pool.push(series);
  }
  if (!pool.length) return [];
  const longest = pool.reduce((best, current) => (current.length > best.length ? current : best), pool[0]);
  const points = longest.map((point, index) => {
    const values = pool
      .map((series) => (index < series.length ? Number(series[index].value || 0) : null))
      .filter((value) => value !== null);
    if (!values.length) return null;
    return {
      label: point.formatted_time || point.formattedTime || String(index + 1),
      value: round(sum(values) / values.length, 2),
    };
  }).filter(Boolean);
  if (points.length <= 8) return points;
  const step = Math.max(Math.floor(points.length / 8), 1);
  return points.filter((_, index) => index % step === 0).slice(-8);
}

function buildSignalCountSeries(signals, referenceTime) {
  const end = new Date(referenceTime);
  const start = new Date(end.getTime() - 6 * CURRENT_WINDOW_MS);
  const buckets = Array.from({ length: 7 }, () => 0);
  const labels = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start.getTime() + index * CURRENT_WINDOW_MS);
    return `${String(date.getUTCMonth() + 1).padStart(2, "0")}-${String(date.getUTCDate()).padStart(2, "0")}`;
  });
  for (const signal of signals) {
    const date = new Date(signal.published_at);
    const diff = Math.floor((Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()) - Date.UTC(start.getUTCFullYear(), start.getUTCMonth(), start.getUTCDate())) / CURRENT_WINDOW_MS);
    if (diff >= 0 && diff < 7) buckets[diff] += 1;
  }
  return buckets.map((value, index) => ({ label: labels[index], value }));
}

function assessTrendDirection(series) {
  if (series.length < 3) return "insufficient";
  const values = series.map((point) => Number(point.value || 0));
  const latest = values[values.length - 1];
  const previousAvg = average(values.slice(-3, -1));
  const earlyAvg = values.length > 2 ? average(values.slice(0, -2)) : previousAvg;
  if (latest >= Math.max(previousAvg * 1.6, earlyAvg * 1.8, 2)) return "spiking";
  if (latest > previousAvg * 1.15) return "rising";
  if (latest < previousAvg * 0.75 && previousAvg > 0) return "cooling";
  if (Math.max(...values) <= 1) return "weak";
  return "steady";
}

function buildTrendSummary({ trendSeries, trendDirection, currentWindowCount, previousWindowCount, hasSearchConfirmation }) {
  if (!trendSeries.length) return "No time trend available yet.";
  if (trendDirection === "spiking") return "Recent points jump sharply above the earlier baseline.";
  if (trendDirection === "rising") return "Recent points are trending upward over the last few intervals.";
  if (trendDirection === "cooling") return "This topic had activity earlier, but the latest interval cooled off.";
  if (trendDirection === "steady") {
    return hasSearchConfirmation ? "Search demand is holding at a relatively stable level." : "Recent intervals are relatively flat without a breakout.";
  }
  if (trendDirection === "weak") return "Signal is present, but the timeline is still thin.";
  return `Current window ${currentWindowCount} vs previous ${previousWindowCount}.`;
}

function buildLabel(topicKey, keywords) {
  const mapped = topicLabelForKey(topicKey);
  if (mapped) return mapped;
  if (keywords.includes("management") || keywords.includes("simulation")) return "Management Sim";
  if (keywords.includes("platformer") || keywords.includes("precision")) return "Precision Platformer";
  if (keywords.includes("shooter")) return "Arcade Shooter";
  if (keywords.includes("card") || keywords.includes("strategy") || keywords.includes("chess")) return "Card Strategy";
  if (keywords.includes("visual") && keywords.includes("novel")) return "Visual Novel Story";
  if (keywords.includes("puzzle")) return "Puzzle Prototype";
  return keywords.slice(0, 2).map((keyword) => keyword.charAt(0).toUpperCase() + keyword.slice(1)).join(" ") || "Untitled Trend";
}

function suggestGameFormats(keywords) {
  const formats = [];
  for (const keyword of keywords) {
    const format = GAME_FORMAT_RULES[keyword];
    if (format && !formats.includes(format)) formats.push(format);
  }
  return formats.length ? formats : ["interactive microgame"];
}

function suggestMarketingHooks(keywords) {
  const hooks = [];
  for (const keyword of keywords) {
    const hook = HOOK_RULES[keyword];
    if (hook && !hooks.includes(hook)) hooks.push(hook);
  }
  return hooks.length ? hooks : ["Turn the trend into a result worth sharing"];
}

function buildNotes({ currentWindowCount, previousWindowCount, baselineWindowAverage, growthRatio, confidenceScore, executionFitScore, classification, spikeRisk }) {
  return [
    `Current 24h signals: ${currentWindowCount}`,
    `Previous 24h signals: ${previousWindowCount}`,
    `Baseline daily average: ${baselineWindowAverage.toFixed(2)}`,
    `Growth ratio vs baseline/previous: ${growthRatio.toFixed(2)}`,
    `Confidence ${confidenceScore.toFixed(1)}, execution fit ${executionFitScore.toFixed(1)}`,
    `Classification: ${classification}; spike risk: ${spikeRisk}`,
  ];
}

function buildEvidence({ signals, platformCounts, currentWindowCount, previousWindowCount, baselineWindowAverage, currentEngagement, previousEngagement, growthRatio, engagementGrowthRatio }) {
  const evidence = [
    `${currentWindowCount} current-window signals vs ${previousWindowCount} in the previous 24h window`,
    `Baseline average is ${baselineWindowAverage.toFixed(2)} signals per day over the prior ${BASELINE_DAYS} days`,
    `Current engagement ${currentEngagement.toFixed(1)} vs previous-window engagement ${previousEngagement.toFixed(1)}`,
    `Signal growth ratio ${growthRatio.toFixed(2)}; engagement growth ratio ${engagementGrowthRatio.toFixed(2)}`,
    `Observed on ${Object.keys(platformCounts).length} platforms: ${Object.keys(platformCounts).sort().join(", ")}`,
  ];
  if (platformCounts.google_trends) evidence.push("Search validation exists via Google Trends");
  const authors = uniqueAuthors(signals);
  if (authors > 1) evidence.push(`Signals come from ${authors} distinct authors or trend IDs`);
  return evidence;
}

function uniqueAuthors(signals) {
  const authors = new Set(signals.map((signal) => signal.author).filter(Boolean));
  return authors.size || new Set(signals.map((signal) => signal.external_id)).size;
}

function extractBlocks(xml, tagName) {
  return Array.from(xml.matchAll(new RegExp(`<${tagName}\\b[^>]*>([\\s\\S]*?)<\\/${tagName}>`, "gi"))).map((match) => match[1]);
}

function firstMatch(value, pattern) {
  const match = pattern.exec(value);
  if (!match) return "";
  return decodeHtmlEntities((match[1] || match[2] || "").trim());
}

function cleanTitle(title) {
  return decodeHtmlEntities(String(title || "").replace(/\s*\[[^\]]+\]\s*/g, " ").replace(/\s+/g, " ").trim());
}

function stripHtml(value) {
  return String(value || "").replace(/<[^>]+>/g, " ");
}

function decodeHtmlEntities(value) {
  return String(value || "")
    .replace(/<!\[CDATA\[(.*?)\]\]>/gs, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;/g, "'")
    .replace(/&#x2F;/gi, "/")
    .replace(/\s+/g, " ");
}

function parseDateSafe(value) {
  const parsed = new Date(String(value || "").trim());
  return Number.isNaN(parsed.getTime()) ? "" : parsed.toISOString();
}

function batched(items, size) {
  const batches = [];
  for (let index = 0; index < items.length; index += size) {
    batches.push(items.slice(index, index + size));
  }
  return batches;
}

function slugify(value) {
  return String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function hashString(value) {
  let hash = 0;
  const input = String(value || "");
  for (let index = 0; index < input.length; index += 1) {
    hash = (hash * 31 + input.charCodeAt(index)) >>> 0;
  }
  return hash.toString(16);
}

function buildBatchId(value) {
  return String(value).replace(/[^0-9]/g, "").slice(0, 20) || String(Date.now());
}

function sum(values) {
  return values.reduce((total, value) => total + Number(value || 0), 0);
}

function average(values) {
  return values.length ? sum(values) / values.length : 0;
}

function round(value, decimals) {
  const factor = 10 ** decimals;
  return Math.round(Number(value || 0) * factor) / factor;
}
