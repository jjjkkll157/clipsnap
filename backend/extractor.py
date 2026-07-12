"""网页内容提取引擎 — 针对性处理各类中文平台"""
from bs4 import BeautifulSoup
import re


def extract_content(html: str, url: str, is_raw_html: bool = False) -> tuple[str, str]:
    """
    从 HTML 中提取标题和正文内容
    返回 (title, cleaned_html)
    """
    soup = BeautifulSoup(html, "lxml")
    
    # 1. 删除无用标签
    for tag in soup.find_all(["script", "style", "nav", "footer", "iframe", "noscript"]):
        tag.decompose()
    
    # 2. 移除常见广告/侧边栏
    for cls in ["sidebar", "advertisement", "ad-", "recommend", "related-posts", "comment", "share-bar"]:
        for tag in soup.find_all(class_=re.compile(cls, re.I)):
            tag.decompose()
    
    # 3. 提取标题
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
        # 清理标题后缀
        title = re.sub(r'\s*[-–|]\s*(知乎|CSDN|博客园|掘金|简书|V2EX|Medium|Dev\.to).*$', '', title)
    
    # 4. 平台特化提取
    content_html = ""
    
    if "zhihu.com" in url:
        content_html = _extract_zhihu(soup)
    elif "weixin.qq.com" in url or "mp.weixin.qq.com" in url:
        content_html = _extract_wechat(soup)
    elif "csdn.net" in url:
        content_html = _extract_csdn(soup)
    elif "juejin.cn" in url:
        content_html = _extract_juejin(soup)
    elif "cnblogs.com" in url:
        content_html = _extract_cnblogs(soup)
    elif "v2ex.com" in url:
        content_html = _extract_v2ex(soup)
    elif "medium.com" in url:
        content_html = _extract_medium(soup)
    elif "github.com" in url:
        content_html = _extract_github(soup)
    else:
        content_html = _extract_generic(soup)
    
    # 5. 兜底：用正文提取算法
    if not content_html or len(content_html) < 100:
        content_html = _extract_generic(soup)
    
    return title, str(content_html)


def _extract_zhihu(soup) -> str:
    """知乎"""
    content = soup.select_one(".RichContent-inner") or soup.select_one(".Post-RichText")
    return str(content) if content else ""


def _extract_wechat(soup) -> str:
    """微信公众号"""
    content = soup.select_one("#js_content") or soup.select_one(".rich_media_content")
    if content:
        # 移除隐藏元素
        for tag in content.find_all(style=re.compile("visibility.*hidden")):
            tag.decompose()
    return str(content) if content else ""


def _extract_csdn(soup) -> str:
    """CSDN"""
    content = soup.select_one("#content_views") or soup.select_one("article")
    if content:
        for tag in content.select(".hide-article-box, .recommend-box"):
            tag.decompose()
    return str(content) if content else ""


def _extract_juejin(soup) -> str:
    """掘金"""
    content = soup.select_one("article.article") or soup.select_one(".markdown-body")
    return str(content) if content else ""


def _extract_cnblogs(soup) -> str:
    """博客园"""
    content = soup.select_one("#cnblogs_post_body") or soup.select_one(".postBody")
    return str(content) if content else ""


def _extract_v2ex(soup) -> str:
    """V2EX"""
    content = soup.select_one(".topic_content") or soup.select_one(".post-content")
    return str(content) if content else ""


def _extract_medium(soup) -> str:
    """Medium"""
    content = soup.select_one("article")
    return str(content) if content else ""


def _extract_github(soup) -> str:
    """GitHub README"""
    content = soup.select_one("article.markdown-body") or soup.select_one(".readme")
    return str(content) if content else ""


def _extract_generic(soup) -> str:
    """通用提取：找最长的文本块"""
    candidates = []
    for tag_name in ["article", "main", ".post-content", ".content", ".post-body", "#content"]:
        if tag_name.startswith(".") or tag_name.startswith("#"):
            el = soup.select_one(tag_name)
        else:
            el = soup.find(tag_name)
        if el:
            text_len = len(el.get_text(strip=True))
            if text_len > 100:
                candidates.append((text_len, el))
    
    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return str(candidates[0][1])
    
    # 最后的兜底：取 body
    body = soup.find("body")
    return str(body) if body else ""
