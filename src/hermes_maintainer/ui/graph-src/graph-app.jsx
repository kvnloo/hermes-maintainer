import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { GraphExplorer } from "./GraphExplorer.jsx";
import { formatNodeHeading, formatNodeKicker, nodeIdMatches } from "./graph-model.js";

let current = { status: "loading", nodes: [], relations: [], campaign: null, source: "live" };
const listeners = new Set();

export function setGraph(payload) {
  current = payload || { status: "ready", nodes: [], relations: [], campaign: null };
  listeners.forEach((fn) => fn(current));
}

function useGraphPayload() {
  const [payload, setPayload] = useState(current);
  useEffect(() => {
    listeners.add(setPayload);
    setPayload(current);
    return () => listeners.delete(setPayload);
  }, []);
  return payload;
}

function MountedExplorer({ onSelect, search, onNavigate }) {
  const payload = useGraphPayload();
  return (
    <GraphExplorer payload={payload} onSelect={onSelect} search={search} onNavigate={onNavigate} />
  );
}

export function mount(container, options = {}) {
  const root = createRoot(container);
  root.render(
    <MountedExplorer
      onSelect={options.onSelect}
      search={options.search}
      onNavigate={options.onNavigate}
    />,
  );
  return { setGraph, unmount: () => root.unmount() };
}

if (typeof window !== "undefined") {
  window.HermesGraph = { mount, setGraph, formatNodeKicker, formatNodeHeading, nodeIdMatches };
}
