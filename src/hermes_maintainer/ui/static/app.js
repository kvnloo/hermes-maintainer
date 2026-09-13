const $ = (s) => document.querySelector(s)
const fmt = new Intl.NumberFormat()

async function get(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

function metricCard(label, value) {
  return `<div class="metric"><div class="value">${fmt.format(Number(value || 0))}</div><div class="label">${label.replaceAll('_',' ')}</div></div>`
}

function rows(items, render) {
  if (!items.length) return '<div class="empty">No data yet. Run a scan.</div>'
  return items.map(render).join('')
}

async function loadMetrics() {
  const h = await get('/api/health')
  $('#metrics').innerHTML = h.metrics.map(m => metricCard(m.metric, m.value)).join('')
}

async function loadCampaigns() {
  const data = await get('/api/campaigns?limit=30')
  $('#campaign-count').textContent = `${data.length} shown`
  $('#campaigns').innerHTML = rows(data, c => `
    <a href="/api/campaigns/${encodeURIComponent(c.id)}" target="_blank">
      <div class="row">
        <div><div class="title">${escapeHtml(c.title)}</div><div class="meta">${escapeHtml(c.summary || '')}</div></div>
        <div class="badge score">${Number(c.score).toFixed(0)}</div>
      </div>
    </a>`)
}

async function loadRootCauses() {
  const data = await get('/api/root-causes')
  $('#root-causes').innerHTML = rows(data.slice(0,18), x => `
    <div class="row"><div><div class="title">${escapeHtml(x.mechanism)}</div><div class="meta">${escapeHtml(x.examples.join(', '))}</div></div><div class="badge">${fmt.format(x.open_issue_count)}</div></div>`)
}

async function loadOptimizer() {
  const data = await get('/api/optimizer/greedy?max_atoms=20')
  $('#optimizer').innerHTML = rows(data.selected.slice(0,20), x => `
    <div class="row"><div><div class="title">${escapeHtml(x.title)}</div><div class="meta">covers ${x.covers.length} issue(s), supersedes ${x.supersedes.length} PR(s)</div></div><div class="badge score">${Number(x.marginal_ratio).toFixed(1)}</div></div>`)
}

let activeKind = 'issue'
async function loadNodes() {
  const data = await get(`/api/nodes?kind=${activeKind}&state=open&limit=250`)
  $('#nodes').innerHTML = rows(data, n => `
    <a href="${n.url || '#'}" target="_blank"><div class="row"><div><div class="title">#${n.number} ${escapeHtml(n.title)}</div><div class="meta">${escapeHtml(n.author || '')} · ${escapeHtml(n.updated_at || '')}</div></div><div class="badge">${n.kind}</div></div></a>`)
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))
}

async function refreshAll() {
  await Promise.all([loadMetrics(), loadCampaigns(), loadRootCauses(), loadOptimizer(), loadNodes()])
}

$('#refresh').addEventListener('click', refreshAll)
document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', async () => {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'))
  btn.classList.add('active')
  activeKind = btn.dataset.kind
  await loadNodes()
}))
refreshAll().catch(err => console.error(err))
