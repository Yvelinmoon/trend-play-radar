const CACHE_KEY = "latest-google-trends-bridge";
const REPORT_CACHE_KEY = "latest-trend-play-radar-report";
const DEBUG_SOURCES_CACHE_KEY = "latest-trend-play-radar-debug-sources";
const REPORT_HISTORY_INDEX_KEY = "trend-play-radar-report-history-index";
const REPORT_HISTORY_PREFIX = "trend-play-radar-report-history:";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(),
      });
    }

    if (url.pathname === "/health") {
      const cached = await getCachedPayload(env);
      const cachedReport = await getCachedReport(env);
      const debugSources = await getDebugSources(env);
      const history = await getReportHistoryIndex(env);
      return jsonResponse({
        ok: true,
        has_cache: Boolean(cached),
        has_report: Boolean(cachedReport),
        cached_at: cached?.cached_at ?? null,
        keyword_count: cached?.records?.length ?? 0,
        report_cached_at: cachedReport?.published_at ?? null,
        report_topic_count: cachedReport?.topics?.length ?? 0,
        debug_sources_cached_at: debugSources?.published_at ?? null,
        debug_platform_count: Object.keys(debugSources?.platforms || {}).length,
        report_history_count: history.length,
      }, 200, {}, "no-store");
    }

    if (url.pathname === "/publish") {
      if (request.method !== "POST") {
        return jsonResponse({ error: "method_not_allowed" }, 405);
      }
      if (request.headers.get("x-bridge-secret") !== env.BRIDGE_SECRET) {
        return jsonResponse({ error: "unauthorized" }, 401);
      }

      try {
        const body = await request.json();
        const payload = normalizePublishedPayload(body);
        await env.BRIDGE_CACHE.put(CACHE_KEY, JSON.stringify(payload));
        return jsonResponse(payload, 200, {}, "no-store");
      } catch (error) {
        return jsonResponse({ error: "publish_failed", detail: error.message }, 400);
      }
    }

    if (url.pathname === "/clear") {
      if (request.method !== "POST") {
        return jsonResponse({ error: "method_not_allowed" }, 405);
      }
      if (request.headers.get("x-bridge-secret") !== env.BRIDGE_SECRET) {
        return jsonResponse({ error: "unauthorized" }, 401);
      }

      try {
        const body = await request.json().catch(() => ({}));
        const targets = normalizeClearTargets(body?.targets);
        const cleared = [];

        if (targets.includes("bridge")) {
          await env.BRIDGE_CACHE.delete(CACHE_KEY);
          cleared.push("bridge");
        }
        if (targets.includes("report")) {
          await env.BRIDGE_CACHE.delete(REPORT_CACHE_KEY);
          cleared.push("report");
        }
        if (targets.includes("debug")) {
          await env.BRIDGE_CACHE.delete(DEBUG_SOURCES_CACHE_KEY);
          cleared.push("debug");
        }
        if (targets.includes("history")) {
          const history = await getReportHistoryIndex(env);
          await Promise.all(
            history.map((entry) => env.BRIDGE_CACHE.delete(`${REPORT_HISTORY_PREFIX}${entry.batch_id}`))
          );
          await env.BRIDGE_CACHE.delete(REPORT_HISTORY_INDEX_KEY);
          cleared.push("history");
        }

        return jsonResponse(
          {
            ok: true,
            cleared,
            cleared_at: new Date().toISOString(),
          },
          200,
          {},
          "no-store"
        );
      } catch (error) {
        return jsonResponse({ error: "clear_failed", detail: error.message }, 400, {}, "no-store");
      }
    }

    if (url.pathname === "/publish-report") {
      if (request.method !== "POST") {
        return jsonResponse({ error: "method_not_allowed" }, 405);
      }
      if (request.headers.get("x-bridge-secret") !== env.BRIDGE_SECRET) {
        return jsonResponse({ error: "unauthorized" }, 401);
      }

      try {
        const body = await request.json();
        const payload = normalizePublishedReport(body);
        await env.BRIDGE_CACHE.put(REPORT_CACHE_KEY, JSON.stringify(payload));
        await writeReportHistory(env, payload);
        return jsonResponse(payload, 200, {}, "no-store");
      } catch (error) {
        return jsonResponse({ error: "publish_report_failed", detail: error.message }, 400);
      }
    }

    if (url.pathname === "/publish-debug-sources") {
      if (request.method !== "POST") {
        return jsonResponse({ error: "method_not_allowed" }, 405);
      }
      if (request.headers.get("x-bridge-secret") !== env.BRIDGE_SECRET) {
        return jsonResponse({ error: "unauthorized" }, 401);
      }

      try {
        const body = await request.json();
        const payload = normalizeDebugSources(body);
        await env.BRIDGE_CACHE.put(DEBUG_SOURCES_CACHE_KEY, JSON.stringify(payload));
        return jsonResponse(payload, 200, {}, "no-store");
      } catch (error) {
        return jsonResponse({ error: "publish_debug_sources_failed", detail: error.message }, 400);
      }
    }

    if (url.pathname === "/report") {
      const cachedReport = await getCachedReport(env);
      if (cachedReport) {
        return jsonResponse(cachedReport, 200, {
          "x-report-cached-at": cachedReport.published_at,
        }, "no-store");
      }
      return jsonResponse({ error: "no_cached_report", detail: "No report JSON has been published yet." }, 502, {}, "no-store");
    }

    if (url.pathname === "/debug-sources") {
      const payload = await getDebugSources(env);
      if (payload) {
        return jsonResponse(payload, 200, {}, "no-store");
      }
      return jsonResponse({ error: "no_debug_sources", detail: "No debug source payload has been published yet." }, 502, {}, "no-store");
    }

    if (url.pathname === "/history-index") {
      const history = await getReportHistoryIndex(env);
      return jsonResponse(history, 200, {}, "no-store");
    }

    if (url.pathname.startsWith("/history/")) {
      const batchId = url.pathname.split("/").pop();
      if (!batchId) {
        return jsonResponse({ error: "missing_batch_id" }, 400);
      }
      const payload = await getHistoryReport(env, batchId);
      if (!payload) {
        return jsonResponse({ error: "history_not_found", detail: `No report found for batch ${batchId}` }, 404, {}, "no-store");
      }
      return jsonResponse(payload, 200, {
        "x-report-batch-id": batchId,
      }, "no-store");
    }

    const cached = await getCachedPayload(env);
    if (cached) {
      return jsonResponse(cached.records, 200, {
        "x-bridge-cached-at": cached.cached_at,
      }, "no-store");
    }

    return jsonResponse({ error: "no_cached_bridge", detail: "No bridge JSON has been published yet." }, 502, {}, "no-store");
  },
};

async function getCachedPayload(env) {
  const raw = await env.BRIDGE_CACHE.get(CACHE_KEY);
  return raw ? JSON.parse(raw) : null;
}

async function getCachedReport(env) {
  const raw = await env.BRIDGE_CACHE.get(REPORT_CACHE_KEY);
  return raw ? JSON.parse(raw) : null;
}

async function getDebugSources(env) {
  const raw = await env.BRIDGE_CACHE.get(DEBUG_SOURCES_CACHE_KEY);
  return raw ? JSON.parse(raw) : null;
}

async function getReportHistoryIndex(env) {
  const raw = await env.BRIDGE_CACHE.get(REPORT_HISTORY_INDEX_KEY);
  return raw ? JSON.parse(raw) : [];
}

async function getHistoryReport(env, batchId) {
  const raw = await env.BRIDGE_CACHE.get(`${REPORT_HISTORY_PREFIX}${batchId}`);
  return raw ? JSON.parse(raw) : null;
}

function normalizePublishedPayload(body) {
  const records = Array.isArray(body) ? body : body?.records;
  if (!Array.isArray(records)) {
    throw new Error("Expected a JSON array or an object with a 'records' array");
  }
  validateBridgeRecords(records);
  return {
    cached_at: new Date().toISOString(),
    records,
  };
}

function normalizePublishedReport(body) {
  const topics = Array.isArray(body) ? body : body?.topics;
  if (!Array.isArray(topics)) {
    throw new Error("Expected a JSON array or an object with a 'topics' array");
  }
  const publishedAt = body?.published_at || new Date().toISOString();
  const batchId = body?.batch_id || buildBatchId(publishedAt);
  return {
    published_at: publishedAt,
    batch_id: batchId,
    topics,
  };
}

function normalizeDebugSources(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new Error("Expected a JSON object");
  }
  return {
    published_at: body.published_at || new Date().toISOString(),
    signal_count: Number(body.signal_count || 0),
    platforms: body.platforms || {},
  };
}

async function writeReportHistory(env, payload) {
  const batchId = payload.batch_id || buildBatchId(payload.published_at);
  await env.BRIDGE_CACHE.put(`${REPORT_HISTORY_PREFIX}${batchId}`, JSON.stringify(payload));

  const current = await getReportHistoryIndex(env);
  const nextEntry = {
    batch_id: batchId,
    published_at: payload.published_at,
    topic_count: payload.topics.length,
    json_path: `/history/${batchId}`,
  };
  const deduped = [nextEntry, ...current.filter((entry) => entry.batch_id !== batchId)].slice(0, 200);
  await env.BRIDGE_CACHE.put(REPORT_HISTORY_INDEX_KEY, JSON.stringify(deduped));
}

function buildBatchId(value) {
  return String(value).replace(/[^0-9]/g, "").slice(0, 20) || String(Date.now());
}

function normalizeClearTargets(targets) {
  if (!Array.isArray(targets) || !targets.length) {
    return ["bridge", "report", "debug", "history"];
  }
  const normalized = Array.from(
    new Set(
      targets
        .map((value) => String(value || "").trim().toLowerCase())
        .filter((value) => ["bridge", "report", "debug", "history"].includes(value))
    )
  );
  return normalized.length ? normalized : ["bridge", "report", "debug", "history"];
}

function validateBridgeRecords(records) {
  for (const record of records) {
    const url = String(record?.url || "");
    const rawPayload = record?.raw_payload || {};
    const series = rawPayload?.series;

    if (url.includes("trends.google.com/example/")) {
      throw new Error("Sample Google Trends URLs are not allowed in production cache");
    }

    if (record?.keyword && url.includes("trends.google.com") && !url.includes("/trends/explore")) {
      throw new Error("Google Trends records must use a real /trends/explore URL");
    }

    if (record?.keyword && rawPayload && Object.keys(rawPayload).length > 0 && !Array.isArray(series)) {
      throw new Error("Google Trends records must include raw_payload.series when publishing to production");
    }
  }
}

function jsonResponse(payload, status = 200, headers = {}, cacheControl = "public, max-age=300") {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": cacheControl,
      ...corsHeaders(),
      ...headers,
    },
  });
}

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type,x-bridge-secret",
  };
}
