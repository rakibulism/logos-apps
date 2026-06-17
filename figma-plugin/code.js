// Brands Logo — Figma plugin (main thread)
// Inserts / replaces / resizes SVG logos fetched by the UI from the repo.

const DEFAULTS = { theme: "system", density: "default", size: 128 };
const DEFAULT_SIZE = 128;   // each logo lives in a square frame of this size
const PAD = 0.84;           // the SVG occupies this fraction of the square (rest = padding)

figma.showUI(__html__, { width: 380, height: 600, themeColors: true });

// ---------- settings persistence (figma.clientStorage) ----------
// Never let a storage hiccup break the rest of the plugin.
async function loadSettings() {
  try {
    const s = await figma.clientStorage.getAsync("bl_settings");
    return Object.assign({}, DEFAULTS, s || {});
  } catch (e) {
    return Object.assign({}, DEFAULTS);
  }
}
async function saveSettings(s) {
  try {
    await figma.clientStorage.setAsync("bl_settings", s);
  } catch (e) { /* ignore */ }
}

// ---------- selection reporting ----------
function selectionInfo() {
  const sel = figma.currentPage.selection;
  if (!sel.length) return { hasSelection: false };
  const n = sel[0];
  return {
    hasSelection: true,
    count: sel.length,
    name: n.name,
    type: n.type,
    width: Math.round(n.width * 100) / 100,
    height: Math.round(n.height * 100) / 100,
  };
}
function postSelection() {
  figma.ui.postMessage(Object.assign({ type: "selection" }, selectionInfo()));
}
figma.on("selectionchange", postSelection);

function placeAtViewportCenter(node) {
  const c = figma.viewport.center;
  node.x = Math.round(c.x - node.width / 2);
  node.y = Math.round(c.y - node.height / 2);
}

// ---------- square logo frames ----------
// Scale a node to fit inside box (preserving its aspect ratio, with padding).
function fitInside(node, boxW, boxH, pad) {
  if (!node.width || !node.height) return;
  const s = Math.min((boxW * pad) / node.width, (boxH * pad) / node.height);
  if (s > 0 && isFinite(s)) node.resize(Math.max(1, node.width * s), Math.max(1, node.height * s));
}
function centerIn(child, frame) {
  child.x = Math.round((frame.width - child.width) / 2);
  child.y = Math.round((frame.height - child.height) / 2);
}
function isLogoFrame(node) {
  return node && node.type === "FRAME" && node.getPluginData("brandsLogo") === "1";
}
// Put a logo SVG inside a frame: fit, center, and scale-with-frame on resize.
function placeLogoInto(frame, svgString, name) {
  for (const k of frame.children.slice()) k.remove();
  const logo = figma.createNodeFromSvg(svgString);
  fitInside(logo, frame.width, frame.height, PAD);
  frame.appendChild(logo);
  centerIn(logo, frame);
  logo.constraints = { horizontal: "SCALE", vertical: "SCALE" };
  frame.name = name;
  frame.setPluginData("logoName", name);
}
// Build a fresh container frame (square, or any W×H for "auto") holding the logo.
function buildLogoFrame(svgString, name, w, h) {
  const W = Math.max(8, Math.round(w || DEFAULT_SIZE));
  const H = Math.max(8, Math.round(h || W));
  const frame = figma.createFrame();
  frame.resize(W, H);
  frame.fills = [];               // transparent container
  frame.clipsContent = false;
  frame.setPluginData("brandsLogo", "1");
  placeLogoInto(frame, svgString, name);
  return frame;
}
// Resolve the requested size into { w, h }. "auto" → the given node's size.
function resolveSize(reqSize, node) {
  if (reqSize === "auto") {
    if (node) return { w: node.width, h: node.height, auto: true };
    return { w: DEFAULT_SIZE, h: DEFAULT_SIZE, auto: true };
  }
  const s = reqSize > 0 ? reqSize : DEFAULT_SIZE;
  return { w: s, h: s, auto: false };
}

// ---------- message handler ----------
figma.ui.onmessage = async (msg) => {
  try {
    switch (msg.type) {
      case "ready": {
        // Sync the current selection first so it never depends on storage.
        postSelection();
        const settings = await loadSettings();
        figma.ui.postMessage({ type: "settings", settings });
        break;
      }

      case "save-settings":
        await saveSettings(msg.settings);
        break;

      case "resize-ui":
        figma.ui.resize(
          Math.max(320, Math.round(msg.width)),
          Math.max(400, Math.round(msg.height))
        );
        break;

      case "get-selection":
        postSelection();
        break;

      case "insert": {
        // "auto" → match the currently selected node's size (if any).
        const selNode = figma.currentPage.selection[0];
        const sz = resolveSize(msg.size, selNode);
        if (msg.size === "auto" && !selNode) {
          figma.notify("Auto size: nothing selected — used " + DEFAULT_SIZE + " px");
        }
        const frame = buildLogoFrame(msg.svg, msg.name, sz.w, sz.h);
        placeAtViewportCenter(frame);
        figma.currentPage.selection = [frame];
        figma.viewport.scrollAndZoomIntoView([frame]);
        figma.notify("Inserted " + msg.name);
        postSelection();
        break;
      }

      case "replace": {
        const sel = figma.currentPage.selection;
        if (!sel.length) {
          figma.notify("Select a layer in the canvas to replace", { error: true });
          break;
        }
        const target = sel[0];
        const sz = resolveSize(msg.size, target); // "auto" → the target's own size

        // Our own logo frame → resize to the requested size, then swap the inner SVG.
        if (isLogoFrame(target)) {
          if (Math.round(target.width) !== Math.round(sz.w) || Math.round(target.height) !== Math.round(sz.h)) {
            target.resize(Math.max(8, Math.round(sz.w)), Math.max(8, Math.round(sz.h)));
          }
          placeLogoInto(target, msg.svg, msg.name);
          figma.currentPage.selection = [target];
          figma.notify("Replaced with " + msg.name);
          postSelection();
          break;
        }

        // Any other node (frame, rectangle, image, …) → drop a logo frame on its slot.
        const parent = target.parent;
        if (!parent || typeof parent.insertChild !== "function") {
          figma.notify("Can't replace this layer here", { error: true });
          break;
        }
        const index = parent.children.indexOf(target);
        const frame = buildLogoFrame(msg.svg, msg.name, sz.w, sz.h);
        if (sz.auto) {
          // match the target exactly — same position and bounds
          frame.x = target.x;
          frame.y = target.y;
        } else {
          // fixed square — center it on the target's slot
          frame.x = Math.round(target.x + (target.width - sz.w) / 2);
          frame.y = Math.round(target.y + (target.height - sz.h) / 2);
        }
        parent.insertChild(index, frame);
        target.remove();
        figma.currentPage.selection = [frame];
        figma.notify("Replaced with " + msg.name);
        postSelection();
        break;
      }

      case "resize": {
        const sel = figma.currentPage.selection;
        if (!sel.length) {
          figma.notify("Select a layer to resize", { error: true });
          break;
        }
        const w = Math.max(1, msg.width);
        const h = Math.max(1, msg.height);
        sel[0].resize(w, h);
        figma.notify("Resized to " + Math.round(w) + " × " + Math.round(h));
        postSelection();
        break;
      }
    }
  } catch (e) {
    figma.notify("Error: " + (e && e.message ? e.message : String(e)), { error: true });
  }
};
