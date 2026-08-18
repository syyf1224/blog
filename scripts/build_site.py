from __future__ import annotations

import html
import re
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "obsidian" / "blog-vault"
OUTPUT = ROOT / "_site"


def parse_frontmatter(source: str) -> tuple[dict[str, str], str]:
    if not source.startswith("---"):
        return {}, source
    parts = source.split("---", 2)
    if len(parts) != 3:
        return {}, source
    metadata: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"\'')
    return metadata, parts[2].lstrip()


def slug_for(path: Path) -> str:
    relative = path.relative_to(CONTENT).with_suffix("")
    if relative.name.lower() == "index" and len(relative.parts) == 1:
        return ""
    pieces = [re.sub(r"[^a-z0-9]+", "-", piece.lower()).strip("-") for piece in relative.parts]
    return "/".join(piece for piece in pieces if piece)


def inline_markdown(value: str) -> str:
    value = html.escape(value, quote=False)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\[\[([^]|]+)\|([^]]+)\]\]", r'<a href="/\1/">\2</a>', value)
    value = re.sub(r"\[\[([^]]+)\]\]", r'<a href="/\1/">\1</a>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value)
    return value


def markdown_to_html(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    in_code = False
    in_list = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_list:
                output.append("</ul>")
                in_list = False
            if in_code:
                output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line:
            flush_paragraph()
            if in_list:
                output.append("</ul>")
                in_list = False
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            if in_list:
                output.append("</ul>")
                in_list = False
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue
        if line.startswith("> "):
            flush_paragraph()
            if in_list:
                output.append("</ul>")
                in_list = False
            output.append(f"<blockquote>{inline_markdown(line[2:])}</blockquote>")
            continue
        if re.match(r"^[-*]\s+", line):
            flush_paragraph()
            if not in_list:
                output.append("<ul>")
                in_list = True
            list_item = re.sub(r"^[-*]\s+", "", line)
            output.append(f"<li>{inline_markdown(list_item)}</li>")
            continue
        if in_list:
            output.append("</ul>")
            in_list = False
        paragraph.append(line)
    flush_paragraph()
    if in_list:
        output.append("</ul>")
    return "\n".join(output)


def page_shell(title: str, body: str, description: str = "", depth: int = 0) -> str:
    safe_title = html.escape(title)
    safe_description = html.escape(description or title, quote=True)
    prefix = "../" * depth
    home_href = prefix or "./"
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{safe_description}">
  <title>{safe_title} — Undefined Field</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
  <div class="site-shell">
    <header class="site-header">
      <a class="site-name" href="{home_href}">UNDEFINED FIELD</a>
      <nav><a href="{home_href}">INDEX</a><a href="{prefix}tools/">TOOLS</a><a href="{prefix}projects/">PROJECTS</a></nav>
    </header>
    {body}
    <footer>UNDEFINED FIELD / UPDATED FROM OBSIDIAN</footer>
  </div>
</body>
</html>'''


def load_documents() -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    for path in sorted(CONTENT.rglob("*.md")):
        relative = path.relative_to(CONTENT)
        if "_templates" in relative.parts or path.name.lower() == "readme.md":
            continue
        metadata, markdown = parse_frontmatter(path.read_text(encoding="utf-8"))
        if metadata.get("draft", "false").lower() == "true" and path.name.lower() != "index.md":
            continue
        documents.append({
            "path": path,
            "metadata": metadata,
            "markdown": markdown,
            "slug": slug_for(path),
            "title": metadata.get("title", path.stem),
            "date": metadata.get("date", ""),
        })
    return documents


def write_document(document: dict[str, object]) -> None:
    path = document["path"]
    assert isinstance(path, Path)
    slug = document["slug"]
    assert isinstance(slug, str)
    if not slug:
        return
    destination = OUTPUT / slug / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = document["metadata"]
    assert isinstance(metadata, dict)
    body = f'''<main class="article-page">
  <div class="article-meta">{html.escape(str(metadata.get("section", "INDEX")).upper())} / {html.escape(str(metadata.get("date", "")))}</div>
  <h1>{html.escape(str(document["title"]))}</h1>
  <article>{markdown_to_html(str(document["markdown"]))}</article>
</main>'''
    destination.write_text(page_shell(str(document["title"]), body, str(metadata.get("description", "")), len(slug.split("/"))), encoding="utf-8")


def write_index(documents: list[dict[str, object]]) -> None:
    index = next((document for document in documents if not document["slug"]), None)
    intro = markdown_to_html(str(index["markdown"])) if index else "<h1>UNDEFINED FIELD</h1>"
    entries = [document for document in documents if document["slug"]]
    entries.sort(key=lambda document: str(document["date"]), reverse=True)
    cards = []
    for document in entries:
        metadata = document["metadata"]
        assert isinstance(metadata, dict)
        cards.append(f'''<a class="entry" href="/{document["slug"]}/">
  <span>{html.escape(str(metadata.get("section", "INDEX")).upper())} / {html.escape(str(document["date"] or "UNDATED"))}</span>
  <strong>{html.escape(str(document["title"]))}</strong>
</a>''')
    listing = "\n".join(cards) or '<div class="empty-state">No published entries yet.</div>'
    body = f'''<main class="home-page">
  <section class="home-intro">{intro}</section>
  <section class="entry-list"><div class="list-label">ALL ENTRIES</div>{listing}</section>
</main>'''
    (OUTPUT / "index.html").write_text(page_shell(str(index["title"]) if index else "Undefined Field", body), encoding="utf-8")


def write_section_pages(documents: list[dict[str, object]]) -> None:
    for section in ("tools", "projects"):
        section_documents = [document for document in documents if str(document["slug"]).startswith(f"{section}/")]
        cards = []
        for document in section_documents:
            metadata = document["metadata"]
            assert isinstance(metadata, dict)
            slug = str(document["slug"])
            cards.append(f'''<a class="entry" href="../{slug}/">
  <span>{html.escape(str(metadata.get("date", "UNDATED")))}</span>
  <strong>{html.escape(str(document["title"]))}</strong>
</a>''')
        listing = "\n".join(cards) or '<div class="empty-state">No published entries yet.</div>'
        body = f'''<main class="section-page">
  <div class="section-heading"><span>SECTION</span><h1>{section.upper()}</h1></div>
  <section class="entry-list">{listing}</section>
</main>'''
        destination = OUTPUT / section / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page_shell(section.upper(), body, depth=1), encoding="utf-8")


def write_assets() -> None:
    assets = OUTPUT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (OUTPUT / ".nojekyll").touch()
    (assets / "style.css").write_text('''
:root { color-scheme: light; --paper:#efeee8; --ink:#151515; --green:#63ff47; --line:2px solid var(--ink); }
* { box-sizing:border-box; }
html,body { margin:0; background:var(--paper); color:var(--ink); font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace; }
body { background-image:linear-gradient(27deg,transparent 49.8%,rgba(21,21,21,.045) 50%,transparent 50.2%),linear-gradient(153deg,transparent 49.8%,rgba(21,21,21,.045) 50%,transparent 50.2%); background-size:165px 110px,190px 135px; }
a { color:inherit; }
.site-shell { max-width:1100px; min-height:100vh; margin:auto; border-inline:var(--line); background:rgba(239,238,232,.92); }
.site-header { display:flex; justify-content:space-between; align-items:center; gap:24px; padding:18px 24px; border-bottom:var(--line); }
.site-name { font-weight:700; text-decoration:none; letter-spacing:.03em; }
nav { display:flex; gap:18px; font-size:12px; } nav a { text-decoration:none; }
.home-page { display:grid; grid-template-columns:minmax(0,1fr) 168px; border-bottom:var(--line); }
.home-intro { min-height:340px; padding:45px 4vw 40px; border-right:3px solid var(--ink); position:relative; overflow:hidden; }
.home-intro:before { content:"∫ ψ* Ĥ ψ dτ = E　　∇·E = ρ/ε₀　　E = mc²　　J2000.0 / AZ 180°"; position:absolute; inset:48% -8% -10%; color:rgba(21,21,21,.2); font-size:18px; line-height:5; transform:rotate(-8deg); filter:blur(.5px); mask-image:linear-gradient(to bottom,transparent 0,#000 25%,rgba(0,0,0,.4) 80%,transparent); }
.home-intro > * { position:relative; z-index:1; }
h1 { max-width:700px; margin:0 0 20px; font:800 clamp(48px,8vw,92px)/.85 system-ui,sans-serif; letter-spacing:-.085em; }
.home-intro p { max-width:520px; padding-left:12px; border-left:8px solid var(--ink); font-family:system-ui,"Noto Sans SC",sans-serif; line-height:1.7; }
.entry-list { display:flex; flex-direction:column; }
.list-label { padding:12px 16px; background:var(--ink); color:var(--paper); border-bottom:var(--line); font-size:12px; }
.entry { min-height:155px; display:flex; flex-direction:column; justify-content:space-between; padding:17px; text-decoration:none; border-bottom:var(--line); background:var(--green); color:var(--ink); }
.entry:nth-child(even) { background:var(--ink); color:var(--paper); }
.entry span { font-size:10px; } .entry strong { font:700 18px/1.15 system-ui,"Noto Sans SC",sans-serif; }
.empty-state { padding:18px; font-size:11px; }
.section-page { min-height:70vh; } .section-heading { padding:48px 24px 36px; border-bottom:var(--line); } .section-heading span { font-size:11px; } .section-heading h1 { margin-top:24px; }
.article-page { max-width:780px; padding:80px 8vw 110px; min-height:70vh; }
.article-meta { font-size:11px; margin-bottom:22px; }
.article-page h1 { font-size:clamp(42px,7vw,78px); letter-spacing:-.07em; }
article { max-width:680px; font-family:system-ui,"Noto Sans SC",sans-serif; font-size:17px; line-height:1.9; }
article h2,article h3 { font-family:inherit; line-height:1.2; margin-top:2.2em; } article code,article pre { font-family:inherit; }
article pre { padding:16px; overflow:auto; background:var(--ink); color:var(--green); line-height:1.5; }
article blockquote { margin-inline:0; padding-left:16px; border-left:8px solid var(--green); }
footer { padding:16px 24px; font-size:10px; }
@media (max-width:700px) { .site-header { align-items:flex-start; flex-direction:column; } .home-page { grid-template-columns:1fr; } .home-intro { border-right:0; border-bottom:3px solid var(--ink); min-height:300px; padding:32px 24px; } .entry-list { display:grid; grid-template-columns:1fr 1fr; } .list-label { grid-column:1 / -1; } .entry { min-height:130px; } .article-page { padding:52px 24px 80px; } }
''', encoding="utf-8")


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    documents = load_documents()
    write_assets()
    write_index(documents)
    write_section_pages(documents)
    for document in documents:
        write_document(document)
    print(f"Built {len(documents) - 1 if documents else 0} published article(s) into {OUTPUT}")


if __name__ == "__main__":
    main()
