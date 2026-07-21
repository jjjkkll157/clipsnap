"""ClipSnap — FastAPI backend"""
import json, re, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

from extractor import extract_content
from converter import html_to_markdown, markdown_to_wechat

app = FastAPI(title="ClipSnap", version="1.0.2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 共享 httpx 客户端（惰性初始化，避免 import 时创建连接池） ──
_http = None


def _get_http():
    global _http
    if _http is None:
        _http = httpx.AsyncClient(
            timeout=15, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
    return _http

# ── 工具函数 ──────────────────────────────────────────
_CJK = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


def count_words(text: str) -> int:
    """中英文混合字数：CJK 按字，拉丁按词"""
    return len(_CJK.findall(text)) + len(_CJK.sub(" ", text).split())


def safe_json_loads(s, default=None):
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _truncate(s: str, n: int) -> str:
    """安全截断，末尾加 …"""
    return s if len(s) <= n else s[:n] + "…"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ── 数据库 ──────────────────────────────────────────────
DB = Path(__file__).parent / "clips.db"


def get_db():
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=3000")
    return c


def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS clips (
            id        TEXT PRIMARY KEY,
            url       TEXT NOT NULL,
            title     TEXT DEFAULT '',
            content_md TEXT NOT NULL,
            source_html TEXT DEFAULT '',
            word_count INTEGER DEFAULT 0,
            tags      TEXT DEFAULT '[]',
            created_at TEXT NOT NULL)""")
        db.commit()

init_db()

# ── 静态文件 ────────────────────────────────────────────
_WEB = Path(__file__).parent.parent / "web"
if _WEB.exists():
    app.mount("/static", StaticFiles(directory=str(_WEB)), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    idx = _WEB / "index.html"
    return idx.read_text("utf-8") if idx.exists() else "<h1>ClipSnap API running</h1>"


# ── API ─────────────────────────────────────────────────

@app.post("/api/clip")
async def clip_page(request: Request):
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid JSON")

    url = body.get("url", "")
    html = body.get("html", "")
    tags = body.get("tags", [])

    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "url required")

    if html:
        title, content_html = extract_content(html, url)
    else:
        try:
            resp = await _get_http().get(url)
            resp.raise_for_status()
            title, content_html = extract_content(resp.text, url)
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise HTTPException(502, str(e))

    md = html_to_markdown(content_html)
    wc = count_words(md)
    cid = str(uuid.uuid4())[:12]
    now = _now()

    with get_db() as db:
        db.execute(
            "INSERT INTO clips VALUES (?,?,?,?,?,?,?,?)",
            (cid, url, title, md, content_html, wc, json.dumps(tags, ensure_ascii=False), now))
        db.commit()

    return {"ok": True, "clip": {
        "id": cid, "url": url, "title": title,
        "content_md": _truncate(md, 3000), "word_count": wc, "tags": tags}}


def _row_to_dict(r, full=False):
    d = {
        "id": r["id"], "url": r["url"], "title": r["title"],
        "content_md": r["content_md"] if full else _truncate(r["content_md"], 500),
        "word_count": r["word_count"],
        "tags": safe_json_loads(r["tags"]),
        "created_at": r["created_at"],
    }
    if full:
        d["source_html"] = r["source_html"]
    return d


@app.get("/api/clips")
def list_clips(q: str = "", limit: int = 50, offset: int = 0):
    with get_db() as db:
        if q:
            rows = db.execute(
                "SELECT * FROM clips WHERE title LIKE ? OR content_md LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (f"%{q}%", f"%{q}%", limit, offset)).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM clips ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)).fetchall()
    return {"clips": [_row_to_dict(r) for r in rows]}


@app.get("/api/clip/{cid}")
def get_clip(cid: str):
    with get_db() as db:
        r = db.execute("SELECT * FROM clips WHERE id = ?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "not found")
    return _row_to_dict(r, full=True)


@app.delete("/api/clip/{cid}")
def delete_clip(cid: str):
    with get_db() as db:
        db.execute("DELETE FROM clips WHERE id = ?", (cid,))
        db.commit()
    return {"ok": True}


@app.post("/api/clip/{cid}/export")
def export_wechat(cid: str):
    with get_db() as db:
        r = db.execute("SELECT * FROM clips WHERE id = ?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "not found")
    return {"title": r["title"], "wechat_md": markdown_to_wechat(r["content_md"])}


@app.get("/api/health")
def health():
    with get_db() as db:
        n = db.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
    return {"status": "ok", "clips_count": n}


# ── 启动 ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🖇️  ClipSnap → http://localhost:8710")
    uvicorn.run(app, host="0.0.0.0", port=8710, log_level="info")
