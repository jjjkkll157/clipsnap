"""ClipSnap 后端 API 服务 — FastAPI"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from extractor import extract_content
from converter import html_to_markdown, markdown_to_wechat

app = FastAPI(title="ClipSnap", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── 数据库 ──────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "clips.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
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
        db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        # 默认 API key
        existing = db.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
        if existing == 0:
            default_key = "clipsnap-" + str(uuid.uuid4())[:8]
            db.execute(
                "INSERT INTO api_keys (key, name, created_at) VALUES (?, ?, ?)",
                (default_key, "default", datetime.utcnow().isoformat()),
            )
            db.commit()
            print(f"🔑 默认 API Key: {default_key}")


init_db()

# ── 静态文件 ────────────────────────────────────────────
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Web 管理面板"""
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

    if not url:
        raise HTTPException(400, "url is required")

    # 提取内容
    if raw_html:
        title, content_html = extract_content(raw_html, url, is_raw_html=True)
    else:
        import httpx
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
        title, content_html = extract_content(resp.text, url)

    # 转 Markdown
    md = html_to_markdown(content_html)

    # 保存
    clip_id = str(uuid.uuid4())[:12]
    with get_db() as db:
        db.execute(
            "INSERT INTO clips (id, url, title, content_md, source_html, word_count, tags, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                clip_id,
                url,
                title,
                md,
                content_html,
                len(md.split()),
                json.dumps(tags, ensure_ascii=False),
                datetime.utcnow().isoformat(),
            ),
        )
        db.commit()

    return JSONResponse(
        {
            "ok": True,
            "clip": {
                "id": clip_id,
                "url": url,
                "title": title,
                "content_md": md[:3000] + ("..." if len(md) > 3000 else ""),
                "word_count": len(md.split()),
                "tags": tags,
            },
        }
    )


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
    return JSONResponse(
        {
            "clips": [
                {
                    "id": r["id"],
                    "url": r["url"],
                    "title": r["title"],
                    "content_md": r["content_md"][:500] + ("..." if len(r["content_md"]) > 500 else ""),
                    "word_count": r["word_count"],
                    "tags": json.loads(r["tags"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        }
    )


@app.get("/api/clip/{clip_id}")
def get_clip(clip_id: str):
    """获取单个收藏的完整内容"""
    with get_db() as db:
        row = db.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Clip not found")
    return JSONResponse(
        {
            "id": row["id"],
            "url": row["url"],
            "title": row["title"],
            "content_md": row["content_md"],
            "source_html": row["source_html"],
            "word_count": row["word_count"],
            "tags": json.loads(row["tags"]),
            "created_at": row["created_at"],
        }
    )


@app.delete("/api/clip/{clip_id}")
def delete_clip(clip_id: str):
    """删除收藏"""
    with get_db() as db:
        db.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        db.commit()
    return {"ok": True}


@app.post("/api/clip/{clip_id}/export")
def export_wechat(clip_id: str):
    """导出为微信公众号 Markdown"""
    with get_db() as db:
        row = db.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Clip not found")
    wechat_md = markdown_to_wechat(row["content_md"])
    return JSONResponse({"title": row["title"], "wechat_md": wechat_md})


@app.get("/api/health")
def health():
    return {"status": "ok", "clips_count": get_db().execute("SELECT COUNT(*) FROM clips").fetchone()[0]}


# ── 启动 ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🖇️  ClipSnap starting on http://localhost:8710")
    print("📋  Dashboard: http://localhost:8710")
    uvicorn.run(app, host="0.0.0.0", port=8710, log_level="info")
