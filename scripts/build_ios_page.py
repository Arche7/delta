"""Собирает webapp/ios.html из docs/ios-shortcut.md (запуск: uv run python scripts/build_ios_page.py).

Страница открывается из Mini App («Ещё» → «Инструкция») и сама подставляет адрес сервера
и личный ключ (он передаётся после # и не уходит на сервер).
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
md = (ROOT / "docs" / "ios-shortcut.md").read_text(encoding="utf-8")


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = t.replace("АДРЕС", '<span class="addr">АДРЕС</span>')
    return t.replace("dk_ваш_ключ", '<span class="key">dk_ваш_ключ</span>')


out, stack, table = [], [], False  # stack: открытые списки [(tag, depth)]


def close_lists(to_depth=-1):
    while stack and stack[-1][1] > to_depth:
        out.append(f"</li></{stack.pop()[0]}>")


for line in md.splitlines():
    s = line.rstrip()
    if s.startswith("|"):
        cells = [c.strip() for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("- "):
            continue
        close_lists()
        if not table:
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            table = True
        else:
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        continue
    if table:
        out.append("</table>")
        table = False
    m = re.match(r"^(\s*)(\d+\.|-) (.*)", s)
    if m:
        depth = 1 if len(m.group(1)) >= 2 else 0
        tag = "ol" if m.group(2)[0].isdigit() else "ul"
        close_lists(depth)
        if stack and stack[-1][1] == depth:
            out.append("</li>")
        else:
            out.append(f"<{tag}>")
            stack.append((tag, depth))
        out.append(f"<li>{inline(m.group(3))}")
        continue
    close_lists()
    if s.startswith("# "):
        out.append(f"<h1>{inline(s[2:])}</h1>")
    elif s.startswith("## "):
        out.append(f"<h2>{inline(s[3:])}</h2>")
    elif s:
        out.append(f"<p>{inline(s)}</p>")
close_lists()
if table:
    out.append("</table>")

PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DELTA — команда iPhone</title>
<style>
:root{--bg:#08061A;--text:#F4F1FF;--text2:rgba(244,241,255,.68);--card:rgba(255,255,255,.06);--bd:rgba(255,255,255,.12);--acc:#C6B4FF}
@media (prefers-color-scheme:light){:root{--bg:#F0EDFB;--text:#160F33;--text2:#575073;--card:rgba(255,255,255,.75);--bd:rgba(40,20,90,.1);--acc:#5A38F5}}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 -apple-system,system-ui,sans-serif;padding:24px 16px 60px}
main{max-width:640px;margin:0 auto}
h1{font-size:26px;line-height:1.2;margin:0 0 12px} h2{font-size:19px;margin:28px 0 8px}
li{margin:4px 0} ol,ul{padding-left:22px}
code{background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:1px 6px;font-size:14px;overflow-wrap:anywhere}
.addr,.key{color:var(--acc);font-weight:700}
table{width:100%;border-collapse:collapse;font-size:14px;margin-top:8px}
th,td{text-align:left;border-top:1px solid var(--bd);padding:8px 6px;vertical-align:top}
.top{background:var(--card);border:1px solid var(--bd);border-radius:18px;padding:14px 16px;margin:0 0 18px;font-size:14px;color:var(--text2)}
</style></head><body><main>
<div class="top" id="top">Адрес сервера и ваш ключ подставлены в инструкцию автоматически.</div>
BODY
</main>
<script>
(function () {
  var k = '';
  try { k = new URLSearchParams(location.hash.slice(1)).get('k') || ''; } catch (e) { k = ''; }
  document.querySelectorAll('.addr').forEach(function (e) { e.textContent = location.origin; });
  if (k) document.querySelectorAll('.key').forEach(function (e) { e.textContent = k; });
  else document.getElementById('top').textContent = 'Адрес подставлен. Ключ получите у бота командой /key и вставьте вместо dk_ваш_ключ.';
})();
</script></body></html>
"""
(ROOT / "webapp" / "ios.html").write_text(PAGE.replace("BODY", "\n".join(out)), encoding="utf-8")
print("webapp/ios.html готов")
