"""ClipSnap 后端 API 服务 — FastAPI"""
import sqlite3
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from extractor import extract_content
from converter import html_to_markdown, markdown_to_wechat

app = FastAPI(title="ClipSnap", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 工具函数 ──────────────────────────────────────────
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


def count_words(text: str) -> int:
    """中英文混合字数统计：CJK 字符按字计，拉丁文按词计"""
    cjk = len(_CJK_RE.findall(text))
    latin = len(re.sub(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]", " ", text).split())
    return cjk + latin


def safe_json_loads(s: str, default=None):
    """安全的 JSON 解析，失败时返回默认值"""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


# ── 数据库 ──────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "clips.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT DEFAULT '',
                content_md TEXT NOT NULL,
                source_html TEXT DEFAULT '',
                word_count INTEGER DEFAULT 0,
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)
        db.commit()


init_db()

# ── 静态文件 ────────────────────────────────────────────
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    web_index = WEB_DIR / "index.html"
    if web_index.exists():
        return web_index.read_text(encoding="utf-8")
    return "<h1>ClipSnap API is running. Dashboard not found.</h1>"


# ── API 路由 ────────────────────────────────────────────


@app.post("/api/clip")
async def clip_page(request: Request):
    """
    抓取网页内容并转为 Markdown
    POST body: { "url": "...", "html": "..." (可选), "tags": [...] (可选) }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    url = body.get("url", "")
    raw_html = body.get("html", "")
    tags = body.get("tags", [])

    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(400, "url is required and must start with http(s)://")

    # 提取内容
    if raw_html:
        title, content_html = extract_content(raw_html, url, is_raw_html=True)
    else:
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            title, content_html = extract_content(resp.text, url)
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, f"目标网站返回错误: {e.response.status_code}")
        except httpx.RequestError as e:
            raise HTTPException(502, f"无法访问目标网站: {str(e)}")

    # 转 Markdown
    md = html_to_markdown(content_html)
    wc = count_words(md)

    # 保存
    clip_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as db:
        db.execute(
            "INSERT INTO clips (id, url, title, content_md, source_html, word_count, tags, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (clip_id, url, title, md, content_html, wc, json.dumps(tags, ensure_ascii=False), now),
        )
        db.commit()

    return JSONResponse({
        "ok": True,
        "clip": {
            "id": clip_id,
            "url": url,
            "title": title,
            "content_md": md[:3000] + ("..." if len(md) > 3000 else ""),
            "word_count": wc,
            "tags": tags,
        },
    })


@app.get("/api/clips")
def list_clips(q: str = "", limit: int = 50, offset: int = 0):
    """列出所有收藏"""
    with get_db() as db:
        if q:
            rows = db.execute(
                "SELECT * FROM clips WHERE title LIKE ? OR content_md LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (f"%{q}%", f"%{q}%", limit, offset),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM clips ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    return JSONResponse({
        "clips": [
            {
                "id": r["id"],
                "url": r["url"],
                "title": r["title"],
                "content_md": r["content_md"][:500] + ("..." if len(r["content_md"]) > 500 else ""),
                "word_count": r["word_count"],
                "tags": safe_json_loads(r["tags"]),
                "created_at": r["created_at"],
                }
                for r in rows
                ]
    })


@app.get("/api/clip/{clip_id}")
def get_clip(clip_id: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Clip not found")
    return JSONResponse({
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "content_md": row["content_md"],
        "source_html": row["source_html"],
        "word_count": row["word_count"],
        "tags": safe_json_loads(row["tags"]),
        "created_at": row["created_at"],
    })


@app.delete("/api/clip/{clip_id}")
def delete_clip(clip_id: str):
    with get_db() as db:
        db.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        db.commit()
    return {"ok": True}


@app.post("/api/clip/{clip_id}/export")
def export_wechat(clip_id: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Clip not found")
    wechat_md = markdown_to_wechat(row["content_md"])
    return JSONResponse({"title": row["title"], "wechat_md": wechat_md})


@app.get("/api/health")
def health():
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
    return {"status": "ok", "clips_count": count}


# ── 启动 ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🖇️  ClipSnap starting on http://localhost:8710")
    print("📋  Dashboard: http://localhost:8710")
    uvicorn.run(app, host="0.0.0.0", port=8710, log_level="info")
