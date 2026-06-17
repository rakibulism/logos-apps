// Brands Logo — Figma plugin (main thread)
// Inserts / replaces / resizes SVG logos fetched by the UI from the repo.

const DEFAULTS = { theme: "system", density: "default" };

figma.showUI(__html__, { width: 380, height: 600, themeColors: true });

// ---------- settings persistence (figma.clientStorage) ----------
async function loadSettings() {
  const s = await figma.clientStorage.getAsync("bl_settings");
  return Object.assign({}, DEFAULTS, s || {});
}
async function saveSettings(s) {
  await figma.clientStorage.setAsync("bl_settings", s);
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

// ---------- message handler ----------
figma.ui.onmessage = async (msg) => {
  try {
    switch (msg.type) {
      case "ready": {
        const settings = await loadSettings();
        figma.ui.postMessage({ type: "settings", settings });
        postSelection();
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
        const node = figma.createNodeFromSvg(msg.svg);
        node.name = msg.name;
        if (msg.width && msg.height) node.resize(msg.width, msg.height);
        placeAtViewportCenter(node);
        figma.currentPage.selection = [node];
        figma.viewport.scrollAndZoomIntoView([node]);
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
        const parent = target.parent;
        if (!parent || typeof parent.insertChild !== "function") {
          figma.notify("Can't replace this layer here", { error: true });
          break;
        }
        const index = parent.children.indexOf(target);
        const node = figma.createNodeFromSvg(msg.svg);
        node.name = msg.name;
        // keep the slot the original occupied (position + bounds)
        node.resize(target.width, target.height);
        node.x = target.x;
        node.y = target.y;
        parent.insertChild(index, node);
        target.remove();
        figma.currentPage.selection = [node];
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
