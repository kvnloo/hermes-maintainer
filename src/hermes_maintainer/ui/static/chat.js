// The browser never speaks ACP directly or receives Hermes credentials. Local API only.
const root = document;
const el = (id) => root.getElementById(id);
const status = el("connection");
const transcript = el("transcript");
const question = el("question");
let mode = "learn";
let chatId = null;
let cursor = 0;
let pollHandle = null;
let pollGeneration = 0;
let busy = false;
let connected = false;
let currentReply = null;

const headers = { "Content-Type": "application/json", "X-Hermes-Maintainer-UI": "1" };
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...headers, ...(options.headers || {}) }, cache: "no-store" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || response.statusText || String(response.status));
  return payload;
}
function connection(message, error = false) {
  status.textContent = message;
  status.classList.toggle("error", error);
}
function appendMessage(role, text = "") {
  transcript.hidden = false;
  root.body.classList.add("in-chat");
  const node = root.createElement("div");
  node.className = "message " + role;
  const badge = root.createElement("span");
  badge.className = "role";
  badge.textContent = role === "user" ? "You" : "Hermes";
  const body = root.createElement("span");
  body.className = "body";
  body.textContent = text;
  node.append(badge, body);
  transcript.append(node);
  node.scrollIntoView({ block: "nearest" });
  return body;
}
function addNote(message, classname = "tool") {
  transcript.hidden = false;
  root.body.classList.add("in-chat");
  const node = root.createElement("div");
  node.className = classname;
  node.textContent = message;
  transcript.append(node);
  node.scrollIntoView({ block: "nearest" });
  return node;
}
function updateUI() {
  el("send").disabled = busy;
  el("cancel").hidden = !busy || !chatId;
  el("new-chat").hidden = !chatId;
  root.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("selected", button.dataset.mode === mode);
    button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
  });
}
function renderPermission(event) {
  const card = addNote("Hermes needs an explicit permission decision.", "permission");
  const text = root.createElement("pre");
  text.textContent = JSON.stringify(event.toolCall || {}, null, 2);
  card.append(text);
  const actions = root.createElement("div");
  actions.className = "actions";
  const offered = new Set((event.options || []).map((option) => option.optionId));
  for (const [optionId, label] of [["deny", "Deny"], ["allow_once", "Allow once"]]) {
    if (!offered.has(optionId)) continue;
    const button = root.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", async () => {
      for (const child of actions.querySelectorAll("button")) child.disabled = true;
      try {
        await api("/api/chat/" + encodeURIComponent(chatId) + "/permission", {
          method: "POST", body: JSON.stringify({ requestId: event.requestId, optionId }),
        });
        card.append(root.createTextNode(" Decision: " + label));
      } catch (error) {
        card.append(root.createTextNode(" " + error.message));
      }
    });
    actions.append(button);
  }
  card.append(actions);
}
function processEvents(events) {
  for (const event of events) {
    if (event.type === "turn_start") {
      currentReply = null;
      busy = true;
      connection("Hermes is working…");
    } else if (event.type === "update") {
      const p = event.payload || {};
      if (p.sessionUpdate === "agent_message_chunk" && p.content?.type === "text") {
        if (!currentReply) currentReply = appendMessage("agent");
        currentReply.textContent += p.content.text || "";
      } else if (p.sessionUpdate === "tool_call" || p.sessionUpdate === "tool_call_update") {
        addNote([p.title || "Tool", p.status || "running"].join(" · "));
      }
    } else if (event.type === "permission") {
      renderPermission(event);
    } else if (event.type === "turn_end") {
      busy = false;
      currentReply = null;
      connection("Hermes ready · " + (event.stopReason || "turn complete"));
    } else if (event.type === "error" || event.type === "disconnected") {
      busy = false;
      currentReply = null;
      addNote(event.message || "Hermes ACP disconnected");
      connection("Hermes connection error", true);
    }
  }
  updateUI();
}
async function poll(sessionId, generation) {
  if (!sessionId || chatId !== sessionId || pollGeneration !== generation) return;
  try {
    const result = await api("/api/chat/" + encodeURIComponent(sessionId) + "/events?cursor=" + cursor);
    if (chatId !== sessionId || pollGeneration !== generation) return;
    cursor = result.cursor;
    processEvents(result.events || []);
  } catch (error) {
    if (chatId !== sessionId || pollGeneration !== generation) return;
    connection(error.message, true);
    busy = false;
    updateUI();
  }
  pollHandle = setTimeout(() => poll(sessionId, generation), 450);
}
async function searchKnowledge(query) {
  const results = el("search-results");
  results.hidden = false;
  let matches;
  try {
    matches = await api("/api/knowledge/search?q=" + encodeURIComponent(query));
  } catch {
    const guides = [
      ["START_HERE.md", "Start here", "contributor issue getting started"],
      ["HERMES_INTENT.md", "Hermes architecture and intent", "session gateway acp model provider"],
      ["TRIAGE_WAVES.md", "Repeatable triage waves", "wave issue triage bugs priority"],
      ["REVIEW_EVIDENCE.md", "Review and test evidence", "pr tests regression review"],
      ["PUBLIC_CASES.md", "Public cases", "case example acp merged salvage"],
      ["SOURCE_POLICY.md", "Source & safety policy", "privacy authority source"],
    ];
    matches = guides.filter((g) => g.join(" ").toLowerCase().includes(query.toLowerCase()) ||
                  query.trim().length > 12).slice(0, 6).map((g) => ({
      title: g[1], path: "./knowledge/" + g[0], excerpt: g[2],
    }));
  }
  results.replaceChildren();
  if (!matches.length) {
    const note = root.createElement("p");
    note.textContent = "No indexed guide matched. Try the starter guide or run Hermes locally.";
    results.append(note);
  }
  for (const hit of matches) {
    const link = root.createElement("a");
    link.className = "result";
    link.href = hit.path;
    const title = root.createElement("strong");
    title.textContent = hit.title;
    const snippet = root.createElement("small");
    snippet.textContent = hit.excerpt || "";
    link.append(title, snippet);
    results.append(link);
  }
  results.scrollIntoView({ block: "nearest" });
}
async function send(value) {
  const text = value.trim();
  if (!text || busy) return;
  question.value = "";
  if (!connected) {
    connection("Public guide search · run the local server to talk to Hermes");
    await searchKnowledge(text);
    return;
  }
  appendMessage("user", text);
  busy = true;
  connection(chatId ? "Sending…" : "Starting a fresh Hermes conversation…");
  updateUI();
  try {
    if (!chatId) {
      const result = await api("/api/chat", { method: "POST", body: JSON.stringify({ prompt: text, mode }) });
      chatId = result.id;
      cursor = 0;
      pollGeneration += 1;
      poll(chatId, pollGeneration);
    } else {
      await api("/api/chat/" + encodeURIComponent(chatId) + "/prompt", {
        method: "POST", body: JSON.stringify({ prompt: text }),
      });
    }
  } catch (error) {
    busy = false;
    addNote(error.message);
    connection("Hermes could not start", true);
  }
  updateUI();
}
el("ask-form").addEventListener("submit", (event) => {
  event.preventDefault();
  send(question.value);
});
question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    el("ask-form").requestSubmit();
  }
});
root.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    if (chatId) return connection("Start a new conversation to change modes");
    mode = button.dataset.mode;
    updateUI();
  });
});
root.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    question.value = button.dataset.example;
    question.focus();
  });
});
el("cancel").addEventListener("click", async () => {
  if (!chatId) return;
  try { await api("/api/chat/" + encodeURIComponent(chatId) + "/cancel", { method: "POST" }); }
  catch (error) { connection(error.message, true); }
});
el("new-chat").addEventListener("click", async () => {
  const oldId = chatId;
  chatId = null;
  pollGeneration += 1;
  cursor = 0;
  busy = false;
  currentReply = null;
  clearTimeout(pollHandle);
  transcript.replaceChildren();
  transcript.hidden = true;
  root.body.classList.remove("in-chat");
  updateUI();
  if (oldId) {
    try { await api("/api/chat/" + encodeURIComponent(oldId), { method: "DELETE" }); }
    catch { /* The local process may already have exited. */ }
  }
  connection("Ready for a new conversation");
  question.focus();
});
(async () => {
  try {
    const state = await api("/api/chat/status");
    connected = state.enabled === true;
    connection(connected ? "Local Hermes ACP configured · approvals required for protected actions" :
                         "Knowledge search only · " + state.message, !connected);
  } catch {
    connection("Public knowledge preview · start hermes-maintainer locally for ACP conversations");
  }
  updateUI();
})();
