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
// Build a fresh square container frame holding the logo.
function buildLogoFrame(svgString, name, size) {
  const S = Math.max(8, Math.round(size || DEFAULT_SIZE));
  const frame = figma.createFrame();
  frame.resize(S, S);
  frame.fills = [];               // transparent container
  frame.clipsContent = false;
  frame.setPluginData("brandsLogo", "1");
  placeLogoInto(frame, svgString, name);
  return frame;
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
        const size = msg.size && msg.size > 0 ? msg.size : DEFAULT_SIZE;
        const frame = buildLogoFrame(msg.svg, msg.name, size);
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

        // Our own square logo frame → just swap the inner SVG, keep the container.
        if (isLogoFrame(target)) {
          placeLogoInto(target, msg.svg, msg.name);
          figma.currentPage.selection = [target];
          figma.notify("Replaced with " + msg.name);
          postSelection();
          break;
        }

        // Any other node → drop in a square logo frame centered on its slot.
        const parent = target.parent;
        if (!parent || typeof parent.insertChild !== "function") {
          figma.notify("Can't replace this layer here", { error: true });
          break;
        }
        const index = parent.children.indexOf(target);
        const S = Math.max(target.width, target.height);
        const frame = buildLogoFrame(msg.svg, msg.name, S);
        frame.x = Math.round(target.x + (target.width - S) / 2);
        frame.y = Math.round(target.y + (target.height - S) / 2);
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
