#!/usr/bin/env python3
"""ObsidianNotes Web Viewer — FastAPI backend."""

import asyncio
import json
import os
import pathlib
import re
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """按优先级查找 user-config.json：
    1. ~/.claude/skills/_shared/user-config.json（安装后用户实际编辑的部署副本）
    2. ../skills/_shared/user-config.json（仓库自带模板）
    找到第一个可解析且 obsidian_vault 存在的就用它。
    """
    candidates = [
        os.path.expanduser("~/.claude/skills/_shared/user-config.json"),
        str(pathlib.Path(__file__).resolve().parent.parent / "skills/_shared/user-config.json"),
    ]
    fallback = {}
    for cfg_path in candidates:
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
        except Exception:
            continue
        if not fallback:
            fallback = cfg
        vault = os.path.expanduser(cfg.get("paths", {}).get("obsidian_vault", ""))
        if vault and os.path.isdir(vault):
            return cfg
    return fallback


CONFIG = load_config()
_PATHS = CONFIG.get("paths", {})


def _resolve_vault() -> str:
    vault = os.path.expanduser(_PATHS.get("obsidian_vault", ""))
    if vault and os.path.isdir(vault):
        return vault
    # 兜底：仓库根目录（clone 后未配置 vault 时至少能启动）
    return str(pathlib.Path(__file__).resolve().parent.parent)


VAULT_PATH = _resolve_vault()
DAILY_DIR = os.path.join(VAULT_PATH, _PATHS.get("daily_papers_folder", "DailyPapers"))
TRENDING_DIR = os.path.join(VAULT_PATH, _PATHS.get("github_trending_folder", "GitHubTrending"))
_NOTES_ROOT = os.path.join(VAULT_PATH, _PATHS.get("paper_notes_folder", "论文笔记"))
NOTES_DIR = os.path.join(_NOTES_ROOT, "_待整理")
CONCEPTS_DIR = os.path.join(_NOTES_ROOT, _PATHS.get("concepts_folder", "_概念"))

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not m:
        return {}, content
    raw = m.group(1)
    body = content[m.end():]
    meta: dict = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().strip('"')
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",")]
            meta[key] = [x for x in items if x]
        elif val.startswith('"') and val.endswith('"'):
            meta[key] = val[1:-1]
        else:
            meta[key] = val
    return meta, body


def parse_tier_table(content: str) -> list[dict]:
    tiers = []
    pattern = re.compile(
        r"^\|\s*(🔥\s*必读|👀\s*值得看|💤\s*可跳过|⚠️\s*关注)\s*\|(.*)\|",
        re.MULTILINE,
    )
    for m in pattern.finditer(content):
        label = m.group(1).strip()
        emoji = label[0]
        name = re.sub(r"^[🔥👀💤⚠️]\s*", "", label)
        papers_raw = m.group(2)
        papers = []
        for seg in papers_raw.split("·"):
            seg = seg.strip()
            wl = re.search(r"\[\[([^\]]+)\]\]", seg)
            desc = re.search(r"[（(](.+?)[）)]", seg)
            if wl:
                pname = wl.group(1)
                papers.append({
                    "name": pname,
                    "description": desc.group(1) if desc else "",
                    "has_note": _note_exists(pname),
                })
        tiers.append({"tier": name, "emoji": emoji, "papers": papers})
    return tiers


def _note_exists(name: str) -> bool:
    for f in os.listdir(NOTES_DIR):
        if f.endswith(".md") and pathlib.Path(f).stem.lower() == name.lower():
            return True
    return False


# ---------------------------------------------------------------------------
# Wikilink index (built at startup)
# ---------------------------------------------------------------------------

WIKILINK_INDEX: dict[str, dict] = {}


def build_wikilink_index():
    global WIKILINK_INDEX
    idx: dict[str, dict] = {}
    # Paper notes
    if os.path.isdir(NOTES_DIR):
        for f in os.listdir(NOTES_DIR):
            if f.endswith(".md") and not f.startswith("_"):
                stem = pathlib.Path(f).stem
                idx[stem] = {"type": "note", "path": f"论文笔记/_待整理/{stem}"}
    # Concepts
    if os.path.isdir(CONCEPTS_DIR):
        for root, _dirs, files in os.walk(CONCEPTS_DIR):
            for f in files:
                if f.endswith(".md"):
                    stem = pathlib.Path(f).stem
                    rel = os.path.relpath(os.path.join(root, f), VAULT_PATH)
                    idx[stem] = {"type": "concept", "path": rel[:-3]}
    # DailyPapers
    if os.path.isdir(DAILY_DIR):
        for f in os.listdir(DAILY_DIR):
            if f.endswith(".md"):
                stem = pathlib.Path(f).stem
                idx[stem] = {"type": "daily", "path": f"DailyPapers/{stem}"}
    WIKILINK_INDEX = idx


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="ObsidianNotes Viewer")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    build_wikilink_index()


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ---- DailyPapers -----------------------------------------------------------

@app.get("/api/daily-papers")
def list_daily_papers():
    if not os.path.isdir(DAILY_DIR):
        return []
    items = []
    for f in sorted(os.listdir(DAILY_DIR), reverse=True):
        if not f.endswith(".md"):
            continue
        fpath = os.path.join(DAILY_DIR, f)
        content = open(fpath, encoding="utf-8").read(2000)
        meta, _ = parse_frontmatter(content)
        dm = re.match(r"(\d{4}-\d{2}-\d{2})", f)
        items.append({
            "filename": pathlib.Path(f).stem,
            "date": dm.group(1) if dm else meta.get("date", ""),
            "is_weekly": "一周" in f or "weekly" in f.lower(),
            "range": meta.get("range", ""),
            "tags": meta.get("tags", []),
        })
    return items


@app.get("/api/daily-papers/{filename}")
def get_daily_paper(filename: str):
    fpath = os.path.join(DAILY_DIR, filename + ".md")
    if not os.path.isfile(fpath):
        return {"error": "not found"}
    content = open(fpath, encoding="utf-8").read()
    meta, body = parse_frontmatter(content)
    return {"frontmatter": meta, "content": body, "tiers": parse_tier_table(content)}


# ---- GitHub Trending -------------------------------------------------------

@app.get("/api/github-trending")
def list_github_trending():
    if not os.path.isdir(TRENDING_DIR):
        return []
    items = []
    for f in sorted(os.listdir(TRENDING_DIR), reverse=True):
        if not f.endswith(".md"):
            continue
        content = open(os.path.join(TRENDING_DIR, f), encoding="utf-8").read(2000)
        meta, _ = parse_frontmatter(content)
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", f)
        items.append({
            "filename": pathlib.Path(f).stem,
            "date": meta.get("date", dm.group(1) if dm else ""),
            "period": meta.get("period", ""),
            "tags": meta.get("tags", []),
        })
    return items


@app.get("/api/github-trending/{filename}")
def get_github_trending(filename: str):
    fpath = os.path.join(TRENDING_DIR, filename + ".md")
    if not os.path.isfile(fpath):
        return {"error": "not found"}
    content = open(fpath, encoding="utf-8").read()
    meta, body = parse_frontmatter(content)
    return {"frontmatter": meta, "content": body}


# ---- Paper Notes -----------------------------------------------------------

@app.get("/api/paper-notes")
def list_paper_notes():
    if not os.path.isdir(NOTES_DIR):
        return []
    items = []
    for f in sorted(os.listdir(NOTES_DIR)):
        if not f.endswith(".md") or f.startswith("_"):
            continue
        fpath = os.path.join(NOTES_DIR, f)
        content = open(fpath, encoding="utf-8").read(2000)
        meta, _ = parse_frontmatter(content)
        items.append({
            "filename": pathlib.Path(f).stem,
            "title": meta.get("title", pathlib.Path(f).stem),
            "method_name": meta.get("method_name", ""),
            "venue": meta.get("venue", ""),
            "year": meta.get("year", ""),
            "tags": meta.get("tags", []),
            "created": meta.get("created", ""),
        })
    return items


@app.get("/api/paper-notes/{filename}")
def get_paper_note(filename: str):
    fpath = os.path.join(NOTES_DIR, filename + ".md")
    if not os.path.isfile(fpath):
        return {"error": "not found"}
    content = open(fpath, encoding="utf-8").read()
    meta, body = parse_frontmatter(content)
    return {"frontmatter": meta, "content": body}


# ---- Concept Wiki ----------------------------------------------------------

@app.get("/api/concepts")
def list_concepts():
    if not os.path.isdir(CONCEPTS_DIR):
        return []
    cats = []
    for d in sorted(os.listdir(CONCEPTS_DIR)):
        dpath = os.path.join(CONCEPTS_DIR, d)
        if not os.path.isdir(dpath):
            continue
        concepts = []
        for f in sorted(os.listdir(dpath)):
            if f.endswith(".md") and f != f"{d}.md":
                concepts.append({"name": pathlib.Path(f).stem, "filename": pathlib.Path(f).stem})
        cats.append({"category_id": d, "name": re.sub(r"^\d+-", "", d), "concepts": concepts})
    return cats


@app.get("/api/concepts/{category}/{filename}")
def get_concept(category: str, filename: str):
    fpath = os.path.join(CONCEPTS_DIR, category, filename + ".md")
    if not os.path.isfile(fpath):
        return {"error": "not found"}
    content = open(fpath, encoding="utf-8").read()
    meta, body = parse_frontmatter(content)
    return {"frontmatter": meta, "content": body}


# ---- Wikilink Index --------------------------------------------------------

@app.get("/api/wikilink-index")
def wikilink_index():
    return WIKILINK_INDEX


# ---- Search ----------------------------------------------------------------

@app.get("/api/search")
def search(q: str = Query("", min_length=1)):
    ql = q.lower()
    results = []

    def scan_dir(dirpath: str, rtype: str):
        if not os.path.isdir(dirpath):
            return
        for root, _dirs, files in os.walk(dirpath):
            for f in files:
                if not f.endswith(".md") or f.startswith("_"):
                    continue
                fpath = os.path.join(root, f)
                stem = pathlib.Path(f).stem
                if ql in stem.lower():
                    results.append({"type": rtype, "filename": stem, "title": stem, "snippet": ""})
                    continue
                try:
                    text = open(fpath, encoding="utf-8").read()
                except Exception:
                    continue
                pos = text.lower().find(ql)
                if pos >= 0:
                    start = max(0, pos - 50)
                    end = min(len(text), pos + len(q) + 80)
                    snippet = text[start:end].replace("\n", " ")
                    meta, _ = parse_frontmatter(text)
                    results.append({
                        "type": rtype,
                        "filename": stem,
                        "title": meta.get("title", stem),
                        "snippet": snippet,
                    })
                if len(results) >= 50:
                    return

    scan_dir(DAILY_DIR, "daily")
    scan_dir(NOTES_DIR, "note")
    scan_dir(CONCEPTS_DIR, "concept")
    return results[:50]


# ---- Claude Integration (SSE) ---------------------------------------------

class ClaudeRequest(BaseModel):
    message: str


@app.post("/api/claude")
async def claude_chat(req: ClaudeRequest):
    async def generate():
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p",
                "--output-format", "stream-json", "--verbose",
                "--max-turns", "10",
                "--dangerously-skip-permissions",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=VAULT_PATH,
            )
            proc.stdin.write(req.message.encode())
            proc.stdin.close()

            import time
            last_event_time = time.time()

            async for raw_line in proc.stdout:
                line = raw_line.decode().strip()
                if not line:
                    continue
                now = time.time()
                try:
                    evt = json.loads(line)
                    etype = evt.get("type", "")

                    if etype == "assistant":
                        msg = evt.get("message", {})
                        content_blocks = msg.get("content", [])
                        for block in content_blocks:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    text = block.get("text", "")
                                    if text:
                                        yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
                                elif block.get("type") == "tool_use":
                                    tool_name = block.get("name", "")
                                    tool_input = block.get("input", {})
                                    detail = ""
                                    if tool_name == "WebFetch":
                                        detail = tool_input.get("url", "")[:80]
                                    elif tool_name == "Read":
                                        detail = tool_input.get("file_path", "").split("/")[-1]
                                    elif tool_name == "Bash":
                                        detail = tool_input.get("command", "")[:60]
                                    elif tool_name == "WebSearch":
                                        detail = tool_input.get("query", "")[:60]
                                    elif tool_name == "Skill":
                                        detail = tool_input.get("skill", "")
                                    elif tool_name == "Write":
                                        detail = tool_input.get("file_path", "").split("/")[-1]
                                    yield f"data: {json.dumps({'type': 'tool', 'tool': tool_name, 'detail': detail})}\n\n"

                    elif etype == "result":
                        text = evt.get("result", "")
                        duration = evt.get("duration_ms", 0)
                        cost = evt.get("total_cost_usd", 0)
                        yield f"data: {json.dumps({'type': 'result', 'text': text, 'done': True, 'duration_ms': duration, 'cost_usd': cost})}\n\n"

                    else:
                        # Forward heartbeat for any other event type so frontend knows we're alive
                        if now - last_event_time > 3:
                            yield f"data: {json.dumps({'type': 'heartbeat', 'event': etype})}\n\n"

                    last_event_time = now

                except json.JSONDecodeError:
                    pass
            await proc.wait()
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    print(f"Vault path: {VAULT_PATH}")
    print(f"Starting server at http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
