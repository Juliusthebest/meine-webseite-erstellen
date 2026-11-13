"""Erzeugt Sprechertext.pdf aus SPRECHERTEXT.md (im Look der Lernclips).

Aufruf: python3 make_pdf.py   (benötigt Node.js mit Playwright + Chromium und die Schrift Montserrat)
"""
import html
import json
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/montserrat/Montserrat-{}.ttf"


def parse(md):
    clips, cur = [], None
    for line in md.splitlines():
        m = re.match(r"## (.+?)\s+\(`(.+?)`, ca\. (.+?) min\)", line)
        if m:
            cur = dict(title=m.group(1), file=m.group(2), dur=m.group(3), lines=[])
            clips.append(cur)
            continue
        m = re.match(r"\*\*(\d+:\d+)\*\*\s+(.+?)\s*$", line)
        if m and cur:
            cur["lines"].append((m.group(1), m.group(2)))
    return clips


def build_html(clips):
    faces = "".join(
        f"@font-face{{font-family:M;font-weight:{w};src:url('file://{FONT.format(n)}')}}"
        for n, w in (("Medium", 500), ("SemiBold", 600), ("Bold", 700), ("ExtraBold", 800)))
    css = faces + """
    @page{size:A4;margin:16mm 16mm 18mm}
    *{box-sizing:border-box}
    body{font-family:M,sans-serif;color:#1f282e;font-weight:500;margin:0;font-size:11pt;line-height:1.5}
    .cover{background:#ebeff2;border-radius:14px;padding:22px 26px;margin-bottom:18px}
    h1{font-weight:800;font-size:24pt;margin:0 0 4px}
    .sub{color:#4a6b87;font-weight:600;font-size:11.5pt}
    .tips{margin:14px 0 0;padding:0;list-style:none;font-size:10pt;color:#3b4850}
    .tips li{margin:4px 0;padding-left:18px;position:relative}
    .tips li:before{content:"";position:absolute;left:0;top:7px;width:8px;height:8px;border-radius:2px;background:#f0a830}
    .clip{break-inside:avoid-page;margin:0 0 16px;border:1px solid #dde3e8;border-radius:12px;overflow:hidden}
    .head{display:flex;align-items:center;gap:12px;background:#3b6790;color:#fff;padding:10px 16px}
    .num{background:#f0a830;color:#1f282e;font-weight:800;border-radius:8px;padding:2px 9px;font-size:11pt}
    .head h2{font-size:14pt;font-weight:700;margin:0;flex:1}
    .meta{font-size:9pt;font-weight:600;opacity:.85;text-align:right}
    table{width:100%;border-collapse:collapse}
    td{padding:7px 14px;vertical-align:top;border-top:1px solid #eef1f4}
    tr:first-child td{border-top:none}
    td.t{width:58px;color:#d35b3a;font-weight:700;font-variant-numeric:tabular-nums}
    td.c{width:26px;padding-left:0;padding-right:4px}
    .box{width:13px;height:13px;border:1.6px solid #9aa8b3;border-radius:3px;margin-top:4px}
    """
    parts = ["<div class='cover'><h1>Sprechertext</h1>",
             "<div class='sub'>Lernclips „Lean Production in der Praxis“ – am Beispiel des Dübelherstellers Fischer</div>",
             "<ul class='tips'>",
             "<li>Für die Clips <b>ohne Ton</b> (Ordner <i>clips/ohne_ton</i>). Spiel den Clip ab und sprich mit.</li>",
             "<li>Die rote Zeit zeigt, wann der Satz im Clip beginnt – dann erscheinen auch die passenden Bilder.</li>",
             "<li>Nach jedem Satz kurz Pause machen. Kleine Abweichungen beim Tempo sind kein Problem.</li>",
             "<li>Das Kästchen kannst du abhaken, wenn der Satz aufgenommen ist.</li></ul></div>"]
    for i, c in enumerate(clips):
        parts.append(f"<div class='clip'><div class='head'><span class='num'>{i + 1}</span><h2>{html.escape(c['title'])}</h2>"
                     f"<div class='meta'>{html.escape(c['file'])}<br>ca. {html.escape(c['dur'])} min</div></div><table>")
        for t, s in c["lines"]:
            parts.append(f"<tr><td class='t'>{t}</td><td>{html.escape(s)}</td><td class='c'><div class='box'></div></td></tr>")
        parts.append("</table></div>")
    return f"<!doctype html><html lang='de'><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(parts)}</body></html>"


def main():
    with open(os.path.join(HERE, "SPRECHERTEXT.md"), encoding="utf-8") as f:
        clips = parse(f.read())
    page_html = build_html(clips)
    out = os.path.join(HERE, "Sprechertext.pdf")
    footer = ("<div style='font-size:8pt;color:#8a98a3;width:100%;text-align:center'>"
              "Seite <span class='pageNumber'></span> von <span class='totalPages'></span></div>")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "sprechertext.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(page_html)
        js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + {json.dumps(src)}, {{ waitUntil: 'load' }});
  await p.pdf({{ path: {json.dumps(out)}, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>', footerTemplate: {json.dumps(footer)} }});
  await b.close();
}})();
"""
        script = os.path.join(tmp, "pdf.js")
        with open(script, "w") as f:
            f.write(js)
        subprocess.run(["node", script], check=True)
    print(out, sum(len(c["lines"]) for c in clips), "Sätze")


if __name__ == "__main__":
    main()
