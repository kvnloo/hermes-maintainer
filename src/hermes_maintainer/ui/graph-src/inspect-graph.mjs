import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BASE = process.env.GRAPH_INSPECT_URL || "http://127.0.0.1:7342";
const OUT = process.env.GRAPH_INSPECT_DIR || "/tmp/graph-inspect";
const ZOOM_STOPS = [0.4, 0.75, 1, 1.5, 2];
const VIEWPORTS = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1920", width: 1920, height: 1080 },
  { name: "mobile-390", width: 390, height: 844, isMobile: true, hasTouch: true },
];

mkdirSync(OUT, { recursive: true });

function issue(findings, viewport, zoom, kind, message, extra = {}) {
  findings.push({ viewport, zoom, kind, message, ...extra });
}

async function openGraph(page, graph = "architecture") {
  await page.goto(`${BASE}/?graph=${graph}`, { waitUntil: "networkidle" });
  const tab = page.locator('.view-tabs [data-view="graph"]');
  if (await tab.count()) await tab.click();
  await page.waitForSelector("button.hm-node", { timeout: 15000 });
  await page.waitForTimeout(500);
}

async function clickOpensDetail(page, locator, findings, viewport, zoom, expectText) {
  await locator.evaluate((el) => {
    el.click();
  });
  const detail = page.getByRole("region", { name: /detail/i });
  try {
    await detail.waitFor({ state: "visible", timeout: 4000 });
  } catch {
    issue(findings, viewport, zoom, "dead-click", "Click did not open detail");
    return false;
  }
  if (expectText) {
    const text = await detail.innerText();
    if (!expectText.test(text)) {
      issue(findings, viewport, zoom, "detail", "Detail copy mismatch", { text: text.slice(0, 240) });
    }
  }
  return true;
}

async function inspectViewport(browser, vp, findings) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    isMobile: Boolean(vp.isMobile),
    hasTouch: Boolean(vp.hasTouch),
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(12000);

  await openGraph(page, "architecture");
  await page.screenshot({ path: join(OUT, `${vp.name}-architecture-initial.png`) });

  const sqlite = page.getByRole("button", { name: /sqlite backlog graph/i }).first();
  await sqlite.waitFor({ state: "visible", timeout: 12000 });
  await clickOpensDetail(page, sqlite, findings, vp.name, "fit", /sqlite/i);

  const zoomButtons = {};
  for (const zoom of ZOOM_STOPS) {
    const btn = page.getByRole("button", { name: `Zoom ${zoom}`, exact: true });
    zoomButtons[zoom] = await btn.boundingBox();
    if (!zoomButtons[zoom]) {
      issue(findings, vp.name, zoom, "clip", `Zoom ${zoom} control has no box`);
    } else if (zoomButtons[zoom].height + 0.5 < 44) {
      issue(findings, vp.name, zoom, "hit-target", `Zoom chip shorter than 44px`, zoomButtons[zoom]);
    }
  }
  const fitBtn = page.getByRole("button", { name: "Fit view", exact: true });
  if (!(await fitBtn.boundingBox())) {
    issue(findings, vp.name, "fit", "clip", "Fit view control is off-screen");
  }

  for (const zoom of ZOOM_STOPS) {
    await page.getByRole("button", { name: `Zoom ${zoom}`, exact: true }).click();
    await page.waitForTimeout(280);
    await page.screenshot({ path: join(OUT, `${vp.name}-z${zoom}.png`) });

    const node = page.getByRole("button", { name: /sqlite backlog graph/i }).first();
    const box = await node.boundingBox();
    if (!box) {
      issue(findings, vp.name, zoom, "clip", "SQLite node has no bounding box");
      continue;
    }
    if (box.height + 0.5 < 44 || box.width + 0.5 < 44) {
      issue(findings, vp.name, zoom, "hit-target", `Hit target ${Math.round(box.width)}×${Math.round(box.height)} < 44px`, { box });
    }
    await clickOpensDetail(page, node, findings, vp.name, zoom, /sqlite/i);
  }

  await page.getByRole("button", { name: "Fit view", exact: true }).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(OUT, `${vp.name}-fit.png`) });
  await clickOpensDetail(page, sqlite, findings, vp.name, "fit-after", /sqlite/i);

  const pane = page.locator(".react-flow__pane").first();
  const paneBox = await pane.boundingBox();
  if (paneBox) {
    const before = await page.evaluate(() => ({ x: window.scrollX, y: window.scrollY }));
    await page.mouse.move(paneBox.x + paneBox.width * 0.55, paneBox.y + paneBox.height * 0.45);
    await page.mouse.down();
    await page.mouse.move(paneBox.x + paneBox.width * 0.35, paneBox.y + paneBox.height * 0.3, { steps: 8 });
    await page.mouse.up();
    const after = await page.evaluate(() => ({ x: window.scrollX, y: window.scrollY }));
    if (after.y - before.y > 8) {
      issue(findings, vp.name, "pan", "scroll-steal", "Pane drag scrolled the page", { before, after });
    }
    await page.keyboard.down("Control");
    await page.mouse.wheel(0, -160);
    await page.keyboard.up("Control");
  }

  await page.keyboard.press("Escape");
  const detail = page.getByRole("region", { name: /detail/i });
  if (await detail.isVisible().catch(() => false)) {
    issue(findings, vp.name, "esc", "escape", "Escape did not close detail");
  }

  await page.getByRole("toolbar", { name: /graph controls/i }).getByRole("button", { name: /^campaigns$/i }).click();
  await page.waitForTimeout(700);
  await page.getByRole("button", { name: "Fit view", exact: true }).click();
  await page.waitForTimeout(400);
  const campaignNode = page.getByRole("button", { name: /ci verdict integrity/i }).first();
  if (await campaignNode.count()) {
    await clickOpensDetail(page, campaignNode, findings, vp.name, "campaign", /campaign/i);
    const edge = page.getByRole("button", { name: /^protects$/i }).first();
    if (await edge.count()) {
      await clickOpensDetail(page, edge, findings, vp.name, "campaign-edge", /protects|relationship|typed/i);
    }
  } else {
    issue(findings, vp.name, "campaign", "empty", "Campaign canvas had no CI verdict node");
  }
  await page.screenshot({ path: join(OUT, `${vp.name}-campaign.png`) });

  if (vp.hasTouch) {
    await page.getByRole("toolbar", { name: /graph controls/i }).getByRole("button", { name: /^architecture$/i }).click();
    await page.waitForTimeout(400);
    const handle = page.getByRole("button", { name: /sqlite backlog graph/i }).first();
    const hb = await handle.boundingBox();
    if (hb) {
      await page.touchscreen.tap(hb.x + hb.width / 2, hb.y + hb.height / 2);
      try {
        await detail.waitFor({ state: "visible", timeout: 4000 });
      } catch {
        issue(findings, vp.name, "touch", "dead-click", "Touch tap did not select architecture node");
      }
    }
    const touchScroll = await page.evaluate(() => {
      const paneEl = document.querySelector(".react-flow__pane, .hm-flow");
      const y0 = window.scrollY;
      if (!paneEl) return { missing: true };
      const ev = new Event("touchmove", { bubbles: true, cancelable: true });
      paneEl.dispatchEvent(ev);
      return { prevented: ev.defaultPrevented, delta: window.scrollY - y0 };
    });
    if (!touchScroll.prevented && touchScroll.delta > 0) {
      issue(findings, vp.name, "touch", "scroll-steal", "Touch move reached page scroll", touchScroll);
    }
    try {
      const cdp = await context.newCDPSession(page);
      const box = paneBox || (await pane.boundingBox());
      if (box) {
        await cdp.send("Input.synthesizePinchGesture", {
          x: box.x + box.width / 2,
          y: box.y + box.height / 2,
          scaleFactor: 1.7,
          relativeSpeed: 400,
        });
        await page.waitForTimeout(300);
        await page.screenshot({ path: join(OUT, `${vp.name}-pinch.png`) });
      }
    } catch (error) {
      issue(findings, vp.name, "pinch", "gesture", error.message);
    }
  }

  await context.close();
}

const browser = await chromium.launch({ headless: true });
const findings = [];
try {
  for (const vp of VIEWPORTS) {
    try {
      await inspectViewport(browser, vp, findings);
    } catch (error) {
      issue(findings, vp.name, "run", "crash", error.message);
    }
  }
} finally {
  await browser.close();
}

const report = { base: BASE, findings, screenshots: OUT };
writeFileSync(join(OUT, "report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (findings.some((item) => ["dead-click", "hit-target", "scroll-steal"].includes(item.kind))) {
  process.exitCode = 2;
}
