const $ = (s) => document.querySelector(s)
const fmt = new Intl.NumberFormat()

const THEMES = {
  default: {
    background: "#041c1c",
    midground: "#ffe6cb",
    warmGlow: "rgba(255, 189, 56, 0.35)",
    noise: "1",
    radius: "0.5rem",
    size: "15px",
  },
  "default-large": {
    background: "#041c1c",
    midground: "#ffe6cb",
    warmGlow: "rgba(255, 189, 56, 0.35)",
    noise: "1",
    radius: "0.5rem",
    size: "18px",
  },
  midnight: {
    background: "#0a0a1f",
    midground: "#d4c8ff",
    warmGlow: "rgba(167, 139, 250, 0.32)",
    noise: "0.8",
    radius: "0.75rem",
    size: "15px",
  },
  ember: {
    background: "#1a0a06",
    midground: "#ffd8b0",
    warmGlow: "rgba(249, 115, 22, 0.38)",
    noise: "1",
    radius: "0.25rem",
    size: "15px",
  },
  mono: {
    background: "#0e0e0e",
    midground: "#eaeaea",
    warmGlow: "rgba(255, 255, 255, 0.1)",
    noise: "0.6",
    radius: "0",
    size: "15px",
  },
  cyberpunk: {
    background: "#040608",
    midground: "#9bffcf",
    warmGlow: "rgba(0, 255, 136, 0.22)",
    noise: "1.2",
    radius: "0",
    size: "15px",
  },
  rose: {
    background: "#1a0f15",
    midground: "#ffd4e1",
    warmGlow: "rgba(249, 168, 212, 0.3)",
    noise: "0.9",
    radius: "1rem",
    size: "15px",
  },
  "nous-blue": {
    background: "#E8F2FD",
    midground: "#0053FD",
    warmGlow: "rgba(0, 83, 253, 0.12)",
    noise: "0",
    radius: "0.5rem",
    size: "15px",
  },
}

const state = {
  view: "board",
  kind: "issue",
  campaignId: null,
  usingSeed: false,
}

async function get(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>'"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[c]))
}

function applyTheme(name) {
  const theme = THEMES[name] || THEMES.default
  const root = document.documentElement
  root.dataset.theme = name in THEMES ? name : "default"
  root.style.setProperty("--background-base", theme.background)
  root.style.setProperty("--background", theme.background)
  root.style.setProperty("--midground-base", theme.midground)
  root.style.setProperty("--midground", theme.midground)
  root.style.setProperty("--warm-glow", theme.warmGlow)
  root.style.setProperty("--noise-opacity", theme.noise)
  root.style.setProperty("--theme-radius", theme.radius)
  root.style.setProperty("--theme-base-size", theme.size)
  localStorage.setItem("hermes-maintainer-theme", root.dataset.theme)
}

function metricCard(label, value) {
  return `<div class="metric"><div class="value">${fmt.format(Number(value || 0))}</div><div class="label">${label.replaceAll("_", " ")}</div></div>`
}

function rows(items, render) {
  if (!items.length) return '<div class="empty">No data yet. Run a scan, or open Graph and load the seed canvas.</div>'
  return items.map(render).join("")
}

function filterParams(extra = {}) {
  const params = new URLSearchParams()
  const kind = $("#filter-kind").value
  const st = $("#filter-state").value
  const priority = $("#filter-priority").value
  const component = $("#filter-component").value
  const blocker = $("#filter-blocker").value
  const age = $("#filter-age").value
  const evidence = $("#filter-evidence").value
  const q = $("#filter-q").value.trim()
  if (kind) params.set("kind", kind)
  if (st) params.set("state", st)
  if (priority) params.set("priority", priority)
  if (component) params.set("component", component)
  if (blocker) params.set("blocker", blocker)
  if (evidence) params.set("evidence_level", evidence)
  if (q) params.set("q", q)
  if (age === "stale") params.set("stale_days", "30")
  else if (age) params.set("updated_within_days", age)
  Object.entries(extra).forEach(([k, v]) => {
    if (v) params.set(k, v)
  })
  return params
}

async function loadMetrics() {
  const h = await get("/api/health")
  $("#metrics").innerHTML = h.metrics.map((m) => metricCard(m.metric, m.value)).join("")
}

async function loadCampaigns() {
  const data = await get("/api/campaigns?limit=30")
  $("#campaign-count").textContent = `${data.length} shown`
  $("#campaigns").innerHTML = rows(data, (c) => `
    <button type="button" class="row campaign-row" data-campaign="${escapeHtml(c.id)}">
      <div><div class="title">${escapeHtml(c.title)}</div><div class="meta">${escapeHtml(c.summary || "")} · ${fmt.format(c.member_count || 0)} members</div></div>
      <div class="badge score">${Number(c.score).toFixed(0)}</div>
    </button>`)
  document.querySelectorAll(".campaign-row").forEach((btn) => {
    btn.addEventListener("click", () => openCampaign(btn.dataset.campaign))
  })
}

async function loadRootCauses() {
  const data = await get("/api/root-causes")
  $("#root-causes").innerHTML = rows(data.slice(0, 18), (x) => `
    <div class="row"><div><div class="title">${escapeHtml(x.mechanism)}</div><div class="meta">${escapeHtml((x.examples || []).join(", "))}</div></div><div class="badge">${fmt.format(x.open_issue_count)}</div></div>`)
}

async function loadOptimizer() {
  const data = await get("/api/optimizer/greedy?max_atoms=20")
  $("#optimizer").innerHTML = rows(data.selected.slice(0, 20), (x) => `
    <div class="row"><div><div class="title">${escapeHtml(x.title)}</div><div class="meta">covers ${x.covers.length} issue(s), supersedes ${x.supersedes.length} PR(s)</div></div><div class="badge score">${Number(x.marginal_ratio).toFixed(1)}</div></div>`)
}

async function loadNodes() {
  const data = await get(`/api/nodes?kind=${state.kind}&state=open&limit=250`)
  $("#nodes").innerHTML = rows(data, (n) => `
    <a href="${n.url || "#"}" target="_blank" rel="noreferrer"><div class="row"><div><div class="title">#${n.number} ${escapeHtml(n.title)}</div><div class="meta">${escapeHtml(n.author || "")} · ${escapeHtml(n.updated_at || "")}</div></div><div class="badge">${n.kind}</div></div></a>`)
}

function setView(view) {
  state.view = view
  document.querySelectorAll(".view-tabs .tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === view)
  })
  $("#board-view").hidden = view !== "board"
  $("#graph-view").hidden = view !== "graph"
  if (view === "graph") loadGraph()
}

function renderDetail(node, payload) {
  const campaign = payload?.campaign
  const relations = (payload?.relations || []).filter((rel) => {
    if (!node) return true
    return rel.src_id === node.id || rel.dst_id === node.id
  })
  const members = payload?.nodes || []
  const title = node
    ? `${node.kind} #${node.number} · ${(node.role || "member").replaceAll("_", " ")}`
    : (campaign?.title || "Campaign")
  const summary = node
    ? `${escapeHtml(node.title || "")}<div class="meta">${escapeHtml(node.state || "")} · ${escapeHtml(node.author || "")}</div>`
    : escapeHtml(campaign?.summary || "Typed relationships with confidence and evidence.")
  const relHtml = relations.length
    ? relations.map((rel) => `
        <div class="rel">
          <div class="title">${escapeHtml(rel.src_id)} → ${escapeHtml(rel.relation_type)} → ${escapeHtml(rel.dst_id)}</div>
          <div class="meta">confidence ${Number(rel.confidence || 0).toFixed(2)} · ${escapeHtml(rel.evidence_level || "reported")}${rel.evidence ? ` · ${escapeHtml(rel.evidence)}` : ""}</div>
        </div>`).join("")
    : '<div class="empty">No typed edges in this slice.</div>'
  const roleHtml = node
    ? ""
    : members.slice(0, 24).map((m) => `
        <div class="row"><div><div class="title">${escapeHtml(m.kind)} #${m.number} ${escapeHtml(m.title || "")}</div><div class="meta">${escapeHtml((m.role || "member").replaceAll("_", " "))}</div></div><div class="badge">${escapeHtml(m.role || "member")}</div></div>`).join("")
  $("#detail-body").innerHTML = `
    <div class="title">${escapeHtml(title)}</div>
    <div class="meta" style="margin:8px 0 12px">${summary}</div>
    ${node && node.url ? `<p><a href="${escapeHtml(node.url)}" target="_blank" rel="noreferrer">Open on GitHub</a></p>` : ""}
    <h2>Typed relationships</h2>
    ${relHtml}
    ${roleHtml ? `<h2 style="margin-top:16px">Roles</h2>${roleHtml}` : ""}
  `
}

async function loadGraph() {
  const banner = $("#graph-banner")
  let data
  if (state.usingSeed) {
    data = await get("/api/graph/demo")
  } else {
    const extra = {}
    if (state.campaignId) extra.campaign_id = state.campaignId
    data = await get(`/api/graph?${filterParams(extra).toString()}`)
    if (!data.nodes || data.nodes.length === 0) {
      data = await get("/api/graph/demo")
      state.usingSeed = true
    }
  }
  banner.hidden = data.source !== "seed"
  banner.textContent = data.source === "seed"
    ? "Showing audit seed campaigns (no live graph yet, or Seed canvas was requested)."
    : (data.campaign ? `Campaign: ${data.campaign.title}` : "Live subgraph")
  if (window.HermesGraph && window.HermesGraph.setGraph) {
    window.HermesGraph.setGraph(data)
  }
  renderDetail(null, data)
  return data
}

async function openCampaign(campaignId) {
  state.campaignId = campaignId
  state.usingSeed = false
  setView("graph")
}

async function loadFilterOptions() {
  const data = await get("/api/filters")
  const select = $("#filter-component")
  const current = select.value
  select.innerHTML = '<option value="">all</option>' + (data.components || []).map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("")
  select.value = current
  const evidence = $("#filter-evidence")
  const currentEv = evidence.value
  if ((data.evidence_levels || []).length) {
    evidence.innerHTML = '<option value="">all</option>' + data.evidence_levels.map((level) => `<option value="${escapeHtml(level)}">${escapeHtml(level.replaceAll("_", " "))}</option>`).join("")
    evidence.value = currentEv
  }
}

async function refreshAll() {
  await Promise.all([
    loadMetrics().catch(() => {}),
    loadCampaigns().catch(() => {}),
    loadRootCauses().catch(() => {}),
    loadOptimizer().catch(() => {}),
    loadNodes().catch(() => {}),
    loadFilterOptions().catch(() => {}),
  ])
  if (state.view === "graph") await loadGraph().catch((err) => console.error(err))
}

function mountGraph() {
  const el = $("#flow")
  if (window.HermesGraph && window.HermesGraph.mount) {
    window.HermesGraph.mount(el, {
      onSelect(node, payload) {
        renderDetail(node, payload)
      },
    })
  } else {
    el.innerHTML = '<div class="graph-empty">xyflow bundle missing. Run <code>./scripts/build-ui.sh</code>.</div>'
  }
}

$("#refresh").addEventListener("click", refreshAll)
$("#theme").addEventListener("change", (e) => applyTheme(e.target.value))
$("#use-seed").addEventListener("click", () => {
  state.usingSeed = true
  state.campaignId = null
  setView("graph")
})
document.querySelectorAll(".view-tabs .tab").forEach((btn) => {
  btn.addEventListener("click", () => setView(btn.dataset.view))
})
document.querySelectorAll("#board-view .tab").forEach((btn) => {
  btn.addEventListener("click", async () => {
    document.querySelectorAll("#board-view .tab").forEach((x) => x.classList.remove("active"))
    btn.classList.add("active")
    state.kind = btn.dataset.kind
    await loadNodes()
  })
})
;["filter-kind", "filter-state", "filter-priority", "filter-component", "filter-blocker", "filter-age", "filter-evidence"].forEach((id) => {
  $(`#${id}`).addEventListener("change", () => {
    state.usingSeed = false
    if (state.view === "graph") loadGraph()
  })
})
let searchTimer
$("#filter-q").addEventListener("input", () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    state.usingSeed = false
    if (state.view === "graph") loadGraph()
  }, 250)
})

const savedTheme = localStorage.getItem("hermes-maintainer-theme") || "default"
$("#theme").value = savedTheme in THEMES ? savedTheme : "default"
applyTheme($("#theme").value)
mountGraph()
refreshAll().catch((err) => console.error(err))
if (location.pathname === "/graph" || location.hash.includes("graph")) setView("graph")
