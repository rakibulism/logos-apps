#!/usr/bin/env python3
"""Build index.html (blockus-style design) from the categorized logo data in gen.py."""
import json, os
import gen  # running gen.py regenerates README.md (and a temp index.html we overwrite below)

# plain titles (no emoji) + lucide icon key for each category
PLAIN = {
    "ai":     ("AI & Machine Learning", "sparkles"),
    "lang":   ("Languages & Runtimes", "code"),
    "fw":     ("Frameworks & UI Libraries", "layers"),
    "dev":    ("Dev Tools, CI/CD & Testing", "wrench"),
    "cloud":  ("Cloud, Hosting & Infrastructure", "cloud"),
    "db":     ("Databases & Data", "database"),
    "design": ("Design & Creative", "palette"),
    "social": ("Social & Communication", "chat"),
    "pay":    ("Payments, Fintech & Crypto", "card"),
    "prod":   ("Productivity & Collaboration", "kanban"),
    "shop":   ("E-commerce & CMS", "cart"),
    "media":  ("Media & Entertainment", "music"),
    "os":     ("OS, Platforms & Browsers", "monitor"),
    "mkt":    ("Analytics, Marketing & CRM", "chart"),
    "sec":    ("Security & Identity", "shield"),
    "web":    ("Web Standards & Protocols", "globe"),
    "corp":   ("Companies & Services", "building"),
    "flags":  ("Flags & Nations", "flag"),
    "sport":  ("Sport & Competitions", "trophy"),
    "other":  ("Others", "box"),
}

cats_js = [
    {"key": k, "name": PLAIN[k][0], "icon": PLAIN[k][1], "items": gen.groups[k]}
    for k, _ in gen.CATS if gen.groups[k]
]
wm = sum(1 for n in gen.files if n.endswith("-wordmark"))

tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site_template.html")
out = (open(tpl_path).read()
       .replace("__CATS__", json.dumps(cats_js))
       .replace("__TOTAL__", f"{gen.total:,}")
       .replace("__ICON_COUNT__", f"{gen.total - wm:,}")
       .replace("__WORDMARK_COUNT__", f"{wm:,}")
       .replace("__CAT_COUNT__", str(len(cats_js)))
       .replace("__ZIP__", gen.ZIP_URL)
       .replace("__URL__", gen.PAGES_URL)
       .replace("__REPO__", gen.REPO))

with open(os.path.join(gen.SRC, "index.html"), "w") as f:
    f.write(out)
print(f"index.html (new design) written: {len(out)/1024:.0f} KB")
