"""网页内容提取引擎 — 8+ 平台适配"""
import re
from bs4 import BeautifulSoup

# 各平台 CSS 选择器（按优先级排列）
_SELECTORS = {
    "zhihu.com":    [".RichContent-inner", ".Post-RichText"],
    "weixin.qq.com":["#js_content", ".rich_media_content"],
    "csdn.net":     ["#content_views", "article"],
    "juejin.cn":    ["article.article", ".markdown-body"],
    "cnblogs.com":  ["#cnblogs_post_body", ".postBody"],
    "v2ex.com":     [".topic_content", ".post-content"],
    "medium.com":   ["article"],
    "github.com":   ["article.markdown-body", ".readme"],
}

_AD_CLASSES = ["sidebar", "advertisement", "ad-", "recommend", "related-posts", "share-bar"]
_SKIP_TAGS  = ["script", "style", "nav", "footer", "iframe", "noscript", "header"]
_TITLE_RE   = re.compile(r'\s*[-–|]\s*(知乎|CSDN|博客园|掘金|简书|V2EX|Medium|Dev\.to).*$')
_HIDDEN_RE  = re.compile(r"visibility\s*:\s*hidden", re.I)

# 通用候选选择器
_GENERIC = ["article", "main", ".post-content", ".content", ".post-body", "#content"]


def extract_content(html: str, url: str) -> tuple[str, str]:
    """返回 (title, cleaned_html)"""
    soup = BeautifulSoup(html, "lxml")

    # 1. 删无用标签
    for t in soup.find_all(_SKIP_TAGS):
        t.decompose()

    # 2. 去广告
    for cls in _AD_CLASSES:
        for t in soup.find_all(class_=re.compile(rf"\b{cls}", re.I)):
            t.decompose()

    # 3. 标题
    title = ""
    if soup.title:
        title = _TITLE_RE.sub("", soup.title.get_text(strip=True))

    # 4. 平台特化（长域名优先，避免 weixin.qq.com 误匹配 mp.weixin.qq.com）
    content = ""
    for domain, selectors in sorted(_SELECTORS.items(), key=lambda x: -len(x[0])):
        if domain in url:
            content = _try_select(soup, selectors)
            break

    # 5. 特殊清理
    if "weixin.qq.com" in url and content:
        soup2 = BeautifulSoup(content, "lxml")
        for t in soup2.find_all(style=_HIDDEN_RE):
            t.decompose()
        content = str(soup2)
    if "csdn.net" in url and content:
        soup2 = BeautifulSoup(content, "lxml")
        for t in soup2.select(".hide-article-box, .recommend-box"):
            t.decompose()
        content = str(soup2)

    # 6. 兜底
    if not content or len(BeautifulSoup(content, "lxml").get_text(strip=True)) < 100:
        content = _extract_generic(soup)

    return title, str(content) if content else ""


def _try_select(soup, selectors):
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return str(el)
    return ""


def _extract_generic(soup) -> str:
    best = ("", 0)
    for sel in _GENERIC:
        el = soup.select_one(sel) if sel.startswith((".", "#")) else soup.find(sel)
        if el:
            n = len(el.get_text(strip=True))
            if n > best[1]:
                best = (str(el), n)
    if best[1] > 100:
        return best[0]
    body = soup.find("body")
    return str(body) if body else ""
